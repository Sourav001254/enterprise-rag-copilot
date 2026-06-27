# src/api/main.py
import logging
import time
import asyncio
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from langgraph.types import Command
import os

from configs.settings import settings
from src.db.postgres import db_manager
from src.memory.memory import checkpoint_manager
from src.cache.redis_cache import redis_cache
from src.retrieval.qdrant_client import qdrant_manager
from src.retrieval.bm25_index import bm25_index
from src.api.schemas import QueryRequest, ChatResponse, SQLApproveRequest, UploadResponse
from src.ingestion.pipeline import IngestionPipeline
from pydantic import BaseModel

class UploadRequest(BaseModel):
    directory_path: str
from src.api.auth import verify_jwt
from src.api.middleware import limiter, RequestTracingMiddleware, JWTExtractionMiddleware
from src.security.pipeline import run_input_pipeline
from src.agents.graph import compile_graph
from src.llm.cost_tracker import cost_tracker
from src.observability.langsmith_setup import setup_langsmith
from src.observability.logfire_setup import setup_logfire
from src.observability.prometheus_setup import setup_prometheus
from src.evals.ab_eval import run_ab_eval

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger(__name__)

# Global graph instance
graph_app = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global graph_app
    
    # Setup Observability
    setup_langsmith()
    
    # Startup
    logger.info("Starting Enterprise Advanced RAG API...")
    await db_manager.connect()
    await checkpoint_manager.initialize()
    await qdrant_manager.setup_collection()
    
    # Sync BM25 index from GCS to ensure pods don't start with empty indexes
    try:
        from google.cloud import storage
        blob = storage.Client().bucket(os.getenv("GCS_BUCKET_NAME", "default-bucket")).blob("bm25_index.json")
        if blob.exists(): blob.download_to_filename("bm25_index.json")
    except Exception as e:
        logger.warning(f"GCS BM25 Sync skipped/failed: {e}")
    bm25_index.load_index() # Loads from json
    
    # Compile Graph
    checkpointer = checkpoint_manager.get_checkpointer()
    graph_app = compile_graph(checkpointer=checkpointer)
    
    yield
    
    # Shutdown
    logger.info("Shutting down API...")
    await checkpoint_manager.close()
    await db_manager.close()

app = FastAPI(title="Enterprise Advanced RAG", lifespan=lifespan)

# Middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(RequestTracingMiddleware)
app.add_middleware(JWTExtractionMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_logfire(app)
setup_prometheus(app)

@app.get("/health")
async def health_check():
    db_ok = db_manager.pool is not None
    redis_ok = await redis_cache.health_check()
    return {"status": "ok", "db": db_ok, "redis": redis_ok}

@app.get("/ready")
async def readiness_check():
    db_ok = db_manager.pool is not None
    redis_ok = await redis_cache.health_check()
    if not (db_ok and redis_ok):
        raise HTTPException(status_code=503, detail="Not ready")
    return {"status": "ready"}

@app.post("/upload", response_model=UploadResponse)
async def upload_endpoint(body: UploadRequest, claims: dict = Depends(verify_jwt)):
    # Path Traversal Prevention
    requested_path = os.path.realpath(body.directory_path)
    allowed_root = os.path.realpath(settings.UPLOAD_ROOT_DIR)
    
    if os.path.commonpath([allowed_root, requested_path]) != allowed_root:
        raise HTTPException(status_code=403, detail="Invalid upload directory path.")
        
    result = await IngestionPipeline.run(requested_path)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return UploadResponse(
        status=result["status"],
        documents_processed=result["documents_processed"],
        chunks_created=result["chunks_created"]
    )

@app.post("/query", response_model=ChatResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_USER}/minute")
async def query_endpoint(request: Request, body: QueryRequest, claims: dict = Depends(verify_jwt)):
    start_time = time.time()
    
    # Input Security Pipeline
    sec_result = await run_input_pipeline(body.query, claims)
    if not sec_result.safe:
        raise HTTPException(status_code=403, detail=f"Security violation: {sec_result.reason}")
        
    config = {"configurable": {"thread_id": body.session_id}}
    
    # Run Graph
    try:
        final_state = await graph_app.ainvoke(
            {"query": sec_result.redacted_query, "original_query": body.query, "user_id": claims.get("sub"), "session_id": body.session_id}, 
            config=config
        )
        
        latency = int((time.time() - start_time) * 1000)
        
        # Cost Tracking
        await cost_tracker.log_query(
            session_id=body.session_id,
            user_id=claims.get("sub"),
            query=body.query,
            intent=final_state.get("intent", "unknown"),
            response=final_state.get("answer", ""),
            latency_ms=latency,
            prompt_tokens=final_state.get("prompt_tokens", 0),
            completion_tokens=final_state.get("tokens_used", 0),
            model="gpt-4o",
            error=final_state.get("error")
        )
        
        return ChatResponse(
            answer=final_state.get("answer", ""),
            sources=final_state.get("sources", []),
            tokens_used=final_state.get("tokens_used", 0),
            latency_ms=latency,
            degraded=final_state.get("degraded", False),
            intent=final_state.get("intent", "rag")
        )
    except Exception as e:
        logger.error(f"Graph execution failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during query processing")

@app.post("/query/stream")
@limiter.limit(f"{settings.RATE_LIMIT_PER_USER}/minute")
async def query_stream_endpoint(request: Request, body: QueryRequest, claims: dict = Depends(verify_jwt)):
    """Feature I: Async Streaming with Progress Events"""
    sec_result = await run_input_pipeline(body.query, claims)
    if not sec_result.safe:
        raise HTTPException(status_code=403, detail=f"Security violation: {sec_result.reason}")
        
    config = {"configurable": {"thread_id": body.session_id}}
    
    async def event_generator():
        try:
            # Stream events from LangGraph
            async for event in graph_app.astream_events(
                {"query": sec_result.redacted_query, "original_query": body.query, "user_id": claims.get("sub"), "session_id": body.session_id}, 
                config=config, 
                version="v2"
            ):
                kind = event["event"]
                name = event["name"]
                
                # Emit stage events based on node execution
                if kind == "on_chain_start" and name in ["intent_router", "hybrid_retrieval", "rerank", "llm_answer", "sql_generate"]:
                    yield f"data: {json.dumps({'stage': name, 'status': 'started'})}\n\n"
                    
                if kind == "on_chain_end" and name in ["intent_router", "hybrid_retrieval", "rerank"]:
                    # We can inject specific data if needed, like docs_found
                    yield f"data: {json.dumps({'stage': name, 'status': 'complete'})}\n\n"
                    
                # If we stream the LLM response
                if kind == "on_chat_model_stream":
                    token = event["data"]["chunk"].content
                    if token:
                        yield f"data: {json.dumps({'stage': 'answer', 'status': 'streaming', 'token': token})}\n\n"
                        
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/sql/approve")
async def sql_approve_endpoint(body: SQLApproveRequest, claims: dict = Depends(verify_jwt)):
    """Resumes the LangGraph thread after human intervention."""
    config = {"configurable": {"thread_id": body.session_id}}
    
    try:
        # Resume the graph by passing the approval result via Command
        final_state = await graph_app.ainvoke(
            Command(resume={"approved": body.approved}),
            config=config
        )
        return {"status": "resumed", "final_state_keys": list(final_state.keys())}
    except Exception as e:
        logger.error(f"Failed to resume graph: {e}")
        raise HTTPException(status_code=500, detail="Failed to resume graph")

@app.post("/eval/run")
async def run_eval_endpoint(claims: dict = Depends(verify_jwt)):
    # Very simplified SSE endpoint for evaluation progress
    async def eval_stream():
        yield f"data: {json.dumps({'progress': 10, 'message': 'Loading dataset...'})}\n\n"
        await asyncio.sleep(1)
        yield f"data: {json.dumps({'progress': 50, 'message': 'Running model queries...'})}\n\n"
        await asyncio.sleep(1)
        yield f"data: {json.dumps({'progress': 90, 'message': 'Computing RAGAS metrics...'})}\n\n"
        
        # Real eval pipeline run
        try:
            results = await run_ab_eval()
            if results:
                yield f"data: {json.dumps({'progress': 100, 'message': 'Done', 'results': results})}\n\n"
            else:
                yield f"data: {json.dumps({'progress': 100, 'message': 'Done', 'results': {'metrics': {}}})}\n\n"
        except Exception as e:
            logger.error(f"Eval failed: {e}")
            yield f"data: {json.dumps({'progress': 100, 'message': 'Error', 'error': str(e)})}\n\n"
            
        yield "data: [DONE]\n\n"
        
    return StreamingResponse(eval_stream(), media_type="text/event-stream")


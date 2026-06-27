import pytest
from unittest.mock import patch, MagicMock
from src.ingestion.chunker import document_chunker
from src.retrieval.base import Document
from src.ingestion.pipeline import IngestionPipeline

def test_chunker_fallback():
    docs = [Document(id="1", content="A very long text " * 100)]
    chunks = document_chunker.chunk(docs)
    assert len(chunks) > 0
    assert chunks[0].id == "1_c0"
    # Ensure chunk size respects max tokens
    assert len(chunks[0].content) < len(docs[0].content)

def test_chunker_small_document():
    docs = [Document(id="2", content="Short document.")]
    chunks = document_chunker.chunk(docs)
    assert len(chunks) == 1
    assert chunks[0].id == "2_c0"
    assert chunks[0].content == "Short document."

def test_chunker_empty_document():
    docs = [Document(id="3", content="")]
    chunks = document_chunker.chunk(docs)
    assert len(chunks) == 0

def test_chunker_multiple_documents():
    docs = [
        Document(id="4", content="First doc content"),
        Document(id="5", content="Second doc content")
    ]
    chunks = document_chunker.chunk(docs)
    assert len(chunks) == 2
    assert chunks[0].id == "4_c0"
    assert chunks[1].id == "5_c0"

@pytest.mark.asyncio
async def test_ingestion_pipeline_run():
    with patch("src.ingestion.pipeline.UnstructuredLoader") as mock_loader, \
         patch("src.ingestion.pipeline.QdrantClient") as mock_qdrant, \
         patch("src.ingestion.pipeline.BM25Encoder") as mock_bm25:
        
        # Mocking unstructured loader
        mock_instance = mock_loader.return_value
        mock_instance.load.return_value = [MagicMock(page_content="Test data", metadata={"source": "test.txt"})]
        
        # We don't want to actually run the DB insertions, just test the pipeline flow
        with patch.object(IngestionPipeline, "_embed_and_store", return_value=None):
            await IngestionPipeline.run("dummy/path")
            mock_loader.assert_called()

@pytest.mark.asyncio
async def test_ingestion_invalid_path():
    with patch("os.path.exists", return_value=False):
        try:
            await IngestionPipeline.run("invalid/path")
        except Exception as e:
            assert "Path does not exist" in str(e) or isinstance(e, FileNotFoundError)

import asyncio
import os
import argparse
from src.ingestion.pipeline import IngestionPipeline
from configs.settings import settings

async def main():
    parser = argparse.ArgumentParser(description="Ingest K8s docs into Enterprise RAG")
    parser.add_argument("--dir", type=str, default="data/raw/k8s_docs", help="Directory containing docs")
    args = parser.parse_args()
    
    if not os.path.exists(args.dir):
        print(f"Directory {args.dir} does not exist. Creating it.")
        os.makedirs(args.dir, exist_ok=True)
        with open(os.path.join(args.dir, "sample.md"), "w") as f:
            f.write("# Sample Kubernetes Doc\nThis is a test document for ingestion.")
            
    print(f"Starting ingestion for {args.dir}...")
    result = await IngestionPipeline.run(args.dir)
    print(f"Ingestion result: {result}")

if __name__ == "__main__":
    asyncio.run(main())

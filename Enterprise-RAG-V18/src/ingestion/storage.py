# src/ingestion/storage.py
import logging
import os
import shutil

logger = logging.getLogger(__name__)

class StorageManager:
    def __init__(self, base_dir: str = "data/raw"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        
    def sync_from_gcs(self, bucket_name: str, prefix: str = ""):
        """Mock GCS sync. In prod, use google-cloud-storage."""
        logger.info(f"Syncing from GCS bucket {bucket_name}/{prefix} to {self.base_dir}")
        # Implementation depends on env
        pass
        
    def get_local_path(self) -> str:
        return self.base_dir

storage_manager = StorageManager()

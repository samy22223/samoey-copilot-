import os
from pathlib import Path
from typing import List, Dict, Any
from fastapi import HTTPException

class FileManager:
    def __init__(self, base_path: str = "workspace"):
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _resolve_path(self, path: str) -> Path:
        full_path = (self.base_path / path).resolve()
        if not str(full_path).startswith(str(self.base_path)):
            raise HTTPException(status_code=403, detail="Access denied")
        return full_path
    
    def list_files(self, path: str = "") -> List[Dict[str, Any]]:
        try:
            dir_path = self._resolve_path(path)
            if not dir_path.exists():
                raise HTTPException(status_code=404, detail="Directory not found")
            if not dir_path.is_dir():
                raise HTTPException(status_code=400, detail="Not a directory")
            
            return [{
                "name": item.name,
                "path": str(item.relative_to(self.base_path)),
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size,
                "modified": item.stat().st_mtime,
            } for item in dir_path.iterdir()]
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

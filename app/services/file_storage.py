import os
import shutil
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings

logger = logging.getLogger(__name__)

class FileStorageService:
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.max_file_size = getattr(settings, 'MAX_UPLOAD_SIZE', 50 * 1024 * 1024)  # 50MB default
        self.allowed_extensions = getattr(settings, 'ALLOWED_EXTENSIONS', 
                                        ['txt', 'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif'])
        
        # Ensure upload directory exists
        os.makedirs(self.upload_dir, exist_ok=True)
        
        # In-memory file database (in production, use a real database)
        self.files_db = []

    def _generate_unique_filename(self, original_filename: str) -> str:
        """Generate a unique filename to prevent conflicts."""
        file_ext = original_filename.rsplit('.', 1)[-1].lower() if '.' in original_filename else ''
        unique_id = str(uuid.uuid4())
        return f"{unique_id}.{file_ext}" if file_ext else unique_id

    def _is_allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed."""
        if '.' not in filename:
            return False
        
        file_ext = filename.rsplit('.', 1)[-1].lower()
        return file_ext in self.allowed_extensions

    async def upload_file(
        self,
        file: UploadFile,
        user_id: int,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload a file to storage."""
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided"
            )
        
        if not self._is_allowed_file(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
            )
        
        # Generate unique filename
        unique_filename = self._generate_unique_filename(file.filename)
        file_path = os.path.join(self.upload_dir, unique_filename)
        
        try:
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            if file_size > self.max_file_size:
                # Remove file if too large
                os.remove(file_path)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File too large. Maximum size: {self.max_file_size // (1024*1024)}MB"
                )
            
            # Create file record
            file_record = {
                "id": len(self.files_db) + 1,
                "user_id": user_id,
                "original_filename": file.filename,
                "stored_filename": unique_filename,
                "file_path": file_path,
                "file_size": file_size,
                "content_type": file.content_type or "application/octet-stream",
                "description": description or "",
                "uploaded_at": datetime.utcnow().isoformat(),
                "downloads": 0
            }
            
            self.files_db.append(file_record)
            logger.info(f"File uploaded: {file.filename} by user {user_id}")
            
            return file_record
            
        except Exception as e:
            # Clean up file if upload failed
            if os.path.exists(file_path):
                os.remove(file_path)
            logger.error(f"Failed to upload file {file.filename}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file"
            )

    async def get_user_files(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get files uploaded by a user."""
        user_files = [
            file for file in self.files_db 
            if file["user_id"] == user_id
        ]
        
        # Sort by upload date (newest first)
        user_files.sort(key=lambda x: x["uploaded_at"], reverse=True)
        
        return user_files[offset:offset + limit]

    async def get_file_info(self, file_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Get file information."""
        for file in self.files_db:
            if file["id"] == file_id and file["user_id"] == user_id:
                return file
        return None

    async def download_file(self, file_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Get file for download."""
        file_info = await self.get_file_info(file_id, user_id)
        if not file_info:
            return None
        
        # Check if file exists on disk
        if not os.path.exists(file_info["file_path"]):
            logger.error(f"File not found on disk: {file_info['file_path']}")
            return None
        
        # Increment download count
        file_info["downloads"] += 1
        
        return {
            "file_path": file_info["file_path"],
            "filename": file_info["original_filename"],
            "content_type": file_info["content_type"],
            "downloads": file_info["downloads"]
        }

    async def delete_file(self, file_id: int, user_id: int) -> bool:
        """Delete a file."""
        for i, file in enumerate(self.files_db):
            if file["id"] == file_id and file["user_id"] == user_id:
                # Remove from database
                del self.files_db[i]
                
                # Remove from disk
                try:
                    if os.path.exists(file["file_path"]):
                        os.remove(file["file_path"])
                        logger.info(f"File deleted: {file['original_filename']} by user {user_id}")
                    else:
                        logger.warning(f"File not found on disk during deletion: {file['file_path']}")
                except Exception as e:
                    logger.error(f"Failed to delete file from disk {file['file_path']}: {str(e)}")
                
                return True
        return False

    async def update_file_description(self, file_id: int, user_id: int, description: str) -> bool:
        """Update file description."""
        for file in self.files_db:
            if file["id"] == file_id and file["user_id"] == user_id:
                file["description"] = description
                logger.info(f"File description updated: {file['original_filename']} by user {user_id}")
                return True
        return False

    async def get_storage_stats(self, user_id: int) -> Dict[str, Any]:
        """Get storage statistics for a user."""
        user_files = [file for file in self.files_db if file["user_id"] == user_id]
        
        total_files = len(user_files)
        total_size = sum(file["file_size"] for file in user_files)
        total_downloads = sum(file["downloads"] for file in user_files)
        
        # Group by file type
        by_type = {}
        for file in user_files:
            file_ext = file["original_filename"].rsplit('.', 1)[-1].lower() if '.' in file["original_filename"] else 'unknown'
            by_type[file_ext] = by_type.get(file_ext, 0) + 1
        
        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "total_downloads": total_downloads,
            "by_file_type": by_type
        }

    async def cleanup_old_files(self, days_old: int = 30) -> int:
        """Clean up files older than specified days."""
        cutoff_date = datetime.utcnow().timestamp() - (days_old * 24 * 60 * 60)
        deleted_count = 0
        
        for i, file in enumerate(list(self.files_db)):
            file_date = datetime.fromisoformat(file["uploaded_at"]).timestamp()
            if file_date < cutoff_date:
                # Remove from database
                self.files_db.remove(file)
                
                # Remove from disk
                try:
                    if os.path.exists(file["file_path"]):
                        os.remove(file["file_path"])
                        deleted_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete old file {file['file_path']}: {str(e)}")
        
        logger.info(f"Cleaned up {deleted_count} files older than {days_old} days")
        return deleted_count

# Global file storage service instance
file_storage_service = FileStorageService()

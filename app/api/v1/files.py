from fastapi import APIRouter, Depends, UploadFile, File
from app.models import User
from app.core.security import get_current_active_user

router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """Upload a file."""
    return {"message": "File uploaded successfully", "filename": file.filename}

@router.get("/")
async def list_files(current_user: User = Depends(get_current_active_user)):
    """List user files."""
    return {"files": []}

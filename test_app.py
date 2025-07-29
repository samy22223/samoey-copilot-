from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

# Initialize FastAPI app
app = FastAPI(
    title="Pinnacle Copilot Test",
    description="Test API for Pinnacle Copilot",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Test endpoint
@app.get("/")
async def read_root():
    return {
        "message": "Welcome to Pinnacle Copilot Test API",
        "status": "success",
        "version": "1.0.0"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "test_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

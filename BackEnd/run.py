"""
Quick start script for running the backend server.
"""
import sys
import os

# Add app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.main import app, settings
import uvicorn

if __name__ == "__main__":
    print("=" * 70)
    print("  Real-Time Quantitative Market Analytics Backend")
    print("=" * 70)
    print(f"  Server: http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"  Docs:   http://{settings.API_HOST}:{settings.API_PORT}/docs")
    print(f"  Health: http://{settings.API_HOST}:{settings.API_PORT}/api/health")
    print("=" * 70)
    print()
    
    # Configure logging to reduce noise
    import logging
    logging.getLogger("websockets.client").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False,
        log_level="info"
    )

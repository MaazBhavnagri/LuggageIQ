"""
Main FastAPI application for LuggageIQ
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from utils.config import Config
from utils.logger import setup_logger
from api.routes import router

logger = setup_logger('api')

# Create FastAPI app
app = FastAPI(
    title="LuggageIQ API",
    description="AI-Powered Competitive Intelligence Dashboard for Amazon Luggage Brands",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting LuggageIQ API...")
    Config.ensure_directories()
    logger.info("API startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down LuggageIQ API...")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "LuggageIQ API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "LuggageIQ API",
        "version": "1.0.0"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "type": type(exc).__name__
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=True,
        log_level="info"
    )

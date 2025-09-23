from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

import os
import logging

from api.config import settings
from api.database import create_tables
from api.routers import assets, analysis, reports

# Import migration function for asset_metadata column (fixes SQLAlchemy reserved name issue)
try:
    from api.migrations.add_metadata_to_assets import migrate_add_metadata_column
except ImportError:
    migrate_add_metadata_column = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting up GymRegister API...")
    
    # Create tables
    create_tables()
    logger.info("Database tables created/verified")
    
    # Run database migrations
    if migrate_add_metadata_column:
        try:
            migrate_add_metadata_column()
        except Exception as e:
            logger.warning(f"Migration warning: {str(e)}")
    
    # Ensure upload directory exists
    os.makedirs(settings.upload_dir, exist_ok=True)
    logger.info(f"Upload directory ready: {settings.upload_dir}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down GymRegister API...")

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception on {request.method} {request.url}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "detail": str(exc) if settings.secret_key == "your-super-secret-key-change-in-production" else "An error occurred"
        }
    )

# Include routers
app.include_router(assets.router)
app.include_router(analysis.router)
app.include_router(reports.router)

# Health check endpoints
@app.get("/", tags=["Health"])
def read_root():
    """Root endpoint"""
    return {
        "message": "GymRegister API",
        "version": settings.api_version,
        "docs": "/docs",
        "status": "operational"
    }

@app.get("/api/health", tags=["Health"])
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.api_version,
        "timestamp": "2024-01-01T00:00:00Z"  # Would be datetime.utcnow() in real app
    }

# API info endpoint
@app.get("/api/info", tags=["Info"])
def api_info():
    """API information"""
    return {
        "title": settings.api_title,
        "version": settings.api_version,
        "description": settings.api_description,
        "endpoints": {
            "assets": "/api/assets",
            "analysis": "/api/analyze",
            "reports": "/api/reports",
            "documentation": "/docs"
        },
        "authentication": {
            "methods": ["API Key", "Bearer Token"],
            "headers": ["X-API-Key", "Authorization: Bearer <token>"]
        }
    }
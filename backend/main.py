"""
FastAPI application entrypoint for REVIVE.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.core.config import settings
from backend.api.v1 import api_router
from backend.core.database import sync_engine, Base

# Initialize tables if not already present
Base.metadata.create_all(sync_engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Autonomous AI Revenue Recovery Decision and Execution System",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API V1
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    return {
        "status": "HEALTHY",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


# Mount Static Frontend if built
dist_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(dist_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Serve exact file if exists, else index.html for SPA routing
        target_path = os.path.join(dist_dir, full_path)
        if os.path.exists(target_path) and os.path.isfile(target_path):
            return FileResponse(target_path)
        return FileResponse(os.path.join(dist_dir, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

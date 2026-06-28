"""FastAPI Application Entry Point."""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db, close_db
from app.api import upload, bgv, email as email_api, tracking, inbound_email


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="Email Statement Service",
    description="Upload edited PDF statements and send them via email with password protection",
    version="1.0.0",
    lifespan=lifespan,
)

# Register API routers FIRST (they take priority over static mount)
app.include_router(upload.router, prefix="/api")
app.include_router(bgv.router, prefix="/api")
app.include_router(email_api.router, prefix="/api")
app.include_router(tracking.router, prefix="/api")
app.include_router(inbound_email.router, prefix="/api")


# Health check
@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


# Mount static files at /static/ prefix for CSS/JS assets
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
static_path = Path(static_dir)
if static_path.exists():
    # Mount for static assets (css, js)
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    # Serve index.html at root
    @app.get("/")
    async def serve_index():
        return FileResponse(str(static_path / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)

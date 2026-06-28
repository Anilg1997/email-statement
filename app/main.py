"""FastAPI Application Entry Point."""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
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

# Mount static files at root so that index.html's relative paths work
# (index.html references css/style.css and js/app.js)
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

# Register API routers
app.include_router(upload.router, prefix="/api")
app.include_router(bgv.router, prefix="/api")
app.include_router(email_api.router, prefix="/api")
app.include_router(tracking.router, prefix="/api")
app.include_router(inbound_email.router, prefix="/api")


# Health check
@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)

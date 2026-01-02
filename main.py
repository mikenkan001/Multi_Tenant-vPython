from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv
from app.core.database import engine, Base
from app.api import api_router
from app.core.logging import setup_logging
from app.core.config import settings

load_dotenv()
print(f"🔧 Database URL: {settings.DATABASE_URL}")
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting FastAPI Multi-Tenant SaaS Backend")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(
    title="Multi-Tenant SaaS API",
    description="High-performance async backend with FastAPI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
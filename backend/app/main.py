from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.router import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Deterministic Security & Policy Enforcement Gateway for BFSI LLM Applications.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration for local frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root level health endpoint alias
@app.get("/health", include_in_schema=False)
async def root_health():
    from app.api.health import health_check
    return await health_check()

# Include versioned API router under /api/v1
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)

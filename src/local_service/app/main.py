from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_health import router as health_router
from app.api.routes_jobs import router as jobs_router
from app.core.config import settings
from app.core.logger import configure_logging
from app.core.progress import display_manager


configure_logging()

app = FastAPI(
    title="scrap-image2.0 local service",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(jobs_router)


@app.on_event("startup")
def on_startup() -> None:
    display_manager.start()


@app.on_event("shutdown")
def on_shutdown() -> None:
    display_manager.stop()

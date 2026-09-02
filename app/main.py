import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import settings
from app.db import init_db_indexes
from app.seed import seed_predefined_users
from app.routes import auth, dashboard, search, watch, cron

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

internal_scheduler = None
if settings.ENABLE_INTERNAL_SCHEDULER:
    from apscheduler.schedulers.background import BackgroundScheduler
    from app.scheduler import check_all_watched_books
    internal_scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing MongoDB indexes...")
    init_db_indexes()

    logger.info("Seeding predefined users...")
    seed_predefined_users()

    if internal_scheduler:
        logger.info(f"Starting internal scheduler (every {settings.POLL_INTERVAL_MINUTES} min)...")
        internal_scheduler.add_job(
            check_all_watched_books,
            'interval',
            minutes=settings.POLL_INTERVAL_MINUTES,
            id="mongo_availability_checker",
            replace_existing=True
        )
        internal_scheduler.start()

    yield

    if internal_scheduler:
        logger.info("Shutting down internal scheduler...")
        internal_scheduler.shutdown(wait=False)

app = FastAPI(
    title="מערכת מעקב זמינות ספרים",
    lifespan=lifespan
)

# Include Routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(search.router)
app.include_router(watch.router)
app.include_router(cron.router)

@app.get("/health")
def health():
    return {"status": "ok", "app": "library-catalog-watcher", "engine": "mongodb"}

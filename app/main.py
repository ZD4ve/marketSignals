from datetime import datetime, timedelta
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler

from app.core.database import init_db
from app.features.insider_trading.tasks import fetch_insider_news_job
from app.features.insider_trading.router import router as insider_trading_router

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
BASE_DIR = Path(__file__).resolve().parent
frontend_dir = BASE_DIR / "frontend"

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Database...")
    init_db()
    
    logger.info("Starting APScheduler...")
    scheduler.add_job(fetch_insider_news_job, 'interval', hours=4, next_run_time=datetime.now() + timedelta(minutes=30))
    scheduler.start()
    
    yield
    
    logger.info("Shutting down APScheduler...")
    scheduler.shutdown()

api = FastAPI(title="BET Data Platform", lifespan=lifespan)
api.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@api.get("/", response_class=FileResponse)
async def root():
    return frontend_dir / "index.html"

api.include_router(insider_trading_router)

def main():
    import uvicorn
    uvicorn.run(api, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()

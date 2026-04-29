from datetime import datetime, timedelta
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.database import init_db
from app.features.insider_trading.tasks import fetch_insider_news_job
from app.features.insider_trading.router import router as insider_trading_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Database...")
    init_db()
    
    logger.info("Starting APScheduler...")
    scheduler.add_job(fetch_insider_news_job, 'interval', hours=4, next_run_time=datetime.now() + timedelta(seconds=5))
    scheduler.start()
    
    yield
    
    logger.info("Shutting down APScheduler...")
    scheduler.shutdown()

api = FastAPI(title="BET Data Platform", lifespan=lifespan)

api.include_router(insider_trading_router)

def main():
    import uvicorn
    uvicorn.run(api, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()

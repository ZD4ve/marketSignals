from datetime import datetime, timedelta
import time
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.database import init_db
from app.features.insider_trading.tasks import fetch_insider_news_job

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Initializing Database...")
    init_db()
    
    logger.info("Starting APScheduler...")
    scheduler = BackgroundScheduler()
    
    # Register jobs from modules
    scheduler.add_job(fetch_insider_news_job, 'interval', hours=4, next_run_time=datetime.now() + timedelta(seconds=5))
    
    scheduler.start()
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    main()

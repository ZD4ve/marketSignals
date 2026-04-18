import logging
from sqlmodel import Session, select
from app.core.database import engine, OpsDocumentLog
from app.core.config import settings
from app.scraper.client import LiferayClient
from app.utils.pdf import download_and_parse_pdf
from app.features.insider_trading.processor import vibe_check, extract_insider_data
from app.features.insider_trading.models import InsiderTrade

logger = logging.getLogger(__name__)

def fetch_insider_news_job():
    logger.info("Starting insider trading job...")
    
    try:
        # 1. Scrape URLs (Dummy list for now)
        client = LiferayClient(settings.BET_BASE_URL)
        # client.authenticate(settings.BET_NEWS_API_URL)
        # response = client.get_news("/hidden_api", {"category": "NEWS_NOT_BET"})
        # urls = parse_urls(response)
        urls = ["https://bet.hu/dummy_insider.pdf"] # Replace with actual logic
        
        with Session(engine) as session:
            for url in urls:
                # 2. Check global ops log
                exists = session.exec(select(OpsDocumentLog).where(OpsDocumentLog.document_url == url)).first()
                if exists:
                    continue
                
                # 3. Download and parse
                try:
                    md_text = download_and_parse_pdf(url)
                    
                    # 4. Vibe check
                    if vibe_check(md_text):
                        # 5. Extract
                        data = extract_insider_data(md_text)
                        
                        # 6. Save data
                        trade = InsiderTrade(**data.model_dump(), document_url=url)
                        session.add(trade)
                    
                    # 7. Update Ops Log
                    log_entry = OpsDocumentLog(document_url=url, module_name="insider_trading", status="SUCCESS")
                    session.add(log_entry)
                    session.commit()
                    
                except Exception as e:
                    logger.error(f"Error processing {url}: {e}")
                    log_entry = OpsDocumentLog(document_url=url, module_name="insider_trading", status="FAILED")
                    session.add(log_entry)
                    session.commit()
                    
    except Exception as e:
        logger.error(f"Job failed: {e}")

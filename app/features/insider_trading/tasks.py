import logging
from sqlmodel import Session, select
from sqlalchemy import inspect, text
from core.database import engine, OpsDocumentLog
from scraper.client import LiferayClient, BET_BASE_URL, BET_NEWS_API_URL
from utils.pdf import download_and_parse_pdf
from features.insider_trading.processor import vibe_check, extract_insider_data
from features.insider_trading.models import InsiderTrade

logger = logging.getLogger(__name__)
INSIDER_TRADES_TABLE = "insider_trades"


def _is_announcement_subpage(url: str) -> bool:
    return "/site/newkib/" in url


def _ensure_insider_trade_schema() -> None:
    inspector = inspect(engine)
    if not inspector.has_table(INSIDER_TRADES_TABLE):
        return

    existing_columns = {column["name"] for column in inspector.get_columns(INSIDER_TRADES_TABLE)}
    nullable_columns = [
        "pdmr_name",
        "role_position",
        "issuer_name",
        "issuer_lei",
        "instrument_description",
        "isin",
        "nature_of_transaction",
        "price_volume",
        "aggregated_volume",
        "weighted_average_price",
        "date_of_transaction",
        "place_of_transaction",
        "published_date",
    ]

    with engine.begin() as connection:
        for column_name in nullable_columns:
            if column_name in existing_columns:
                connection.execute(
                    text(f"ALTER TABLE {INSIDER_TRADES_TABLE} ALTER COLUMN {column_name} DROP NOT NULL")
                )

        if "has_missing_fields" not in existing_columns:
            connection.execute(
                text(
                    f"ALTER TABLE {INSIDER_TRADES_TABLE} ADD COLUMN has_missing_fields BOOLEAN NOT NULL DEFAULT FALSE"
                )
            )
            
        if "published_date" not in existing_columns:
            connection.execute(
                text(
                    f"ALTER TABLE {INSIDER_TRADES_TABLE} ADD COLUMN published_date TIMESTAMP NULL"
                )
            )

def fetch_insider_news_job():
    logger.info("Starting insider trading job...")

    try:
        _ensure_insider_trade_schema()

        with LiferayClient(BET_BASE_URL) as client:
            context = client.get_solr_search_context(BET_NEWS_API_URL)

            processed_new_documents = 0
            failed_documents = 0
            stale_pages = 0

            with Session(engine) as session:
                archive_marker = session.exec(
                    select(OpsDocumentLog).where(
                        OpsDocumentLog.module_name == "insider_trading",
                        OpsDocumentLog.document_url == "__insider_trading_full_archive_completed__",
                    )
                ).first()
                is_full_archive_completed = archive_marker is not None
                perform_full_archive_scan = not is_full_archive_completed
                stopped_early = False

                logger.info(
                    "Insider trading crawl starting in %s mode",
                    "full archive" if perform_full_archive_scan else "incremental",
                )

                for page_index, page_payload in client.iterate_solr_pages(
                    context=context,
                    category="NEWS_NOT_BET",
                    query="*",
                    order_mode="DATE_DESC",
                ):
                    page_count = page_payload.get("pageCount") if isinstance(page_payload, dict) else None
                    logger.info(
                        "Processing page %s%s",
                        page_index,
                        f" of {page_count}" if isinstance(page_count, int) else "",
                    )
                    raw_items = client.extract_result_items(page_payload)
                    subpages = [item for item in raw_items if _is_announcement_subpage(item["url"])]
                    if not subpages:
                        continue

                    page_has_new_documents = False

                    for subpage_data in subpages:
                        subpage = subpage_data["url"]
                        published_date = subpage_data["published_date"]
                        absolute_subpage = client.to_absolute_url(subpage)
                        
                        exists = session.exec(
                            select(OpsDocumentLog).where(OpsDocumentLog.document_url == absolute_subpage)
                        ).first()
                        if exists:
                            continue

                        page_has_new_documents = True

                        try:
                            pdf_urls = client.get_pdf_urls_from_announcement_subpage(absolute_subpage)
                            
                            if not pdf_urls:
                                continue
                                
                            md_texts = []
                            for pdf_url in pdf_urls:
                                md_texts.append(download_and_parse_pdf(pdf_url))
                            
                            md_text = "\n\n---\n\n".join(md_texts)

                            if vibe_check(md_text):
                                extraction = extract_insider_data(md_text)
                                if extraction.is_insider_trading:
                                    if extraction.insider_trade is None:
                                        raise ValueError("Missing insider_trade payload for insider document.")

                                    missing_fields = extraction.insider_trade.missing_fields()
                                    trade_data = extraction.insider_trade.model_dump()
                                    trade_data["has_missing_fields"] = bool(missing_fields)
                                    trade_data["published_date"] = published_date
                                    trade = InsiderTrade(
                                        **trade_data,
                                        document_url=absolute_subpage,
                                    )
                                    session.add(trade)

                                    if missing_fields:
                                        logger.info(
                                            "Persisted partial extraction for %s with missing fields: %s",
                                            absolute_subpage,
                                            ", ".join(missing_fields),
                                        )
                                else:
                                    logger.info(
                                        "LLM marked %s as non-insider with certainty %.2f. Reason: %s",
                                        absolute_subpage,
                                        extraction.certainty,
                                        extraction.non_insider_reason,
                                    )

                            log_entry = OpsDocumentLog(
                                document_url=absolute_subpage,
                                module_name="insider_trading",
                                status="SUCCESS",
                            )
                            session.add(log_entry)
                            session.commit()
                            processed_new_documents += 1
                        except Exception as exc:
                            logger.error("Error processing %s: %s", absolute_subpage, exc)
                            log_entry = OpsDocumentLog(
                                document_url=absolute_subpage,
                                module_name="insider_trading",
                                status="FAILED",
                            )
                            session.add(log_entry)
                            session.commit()
                            failed_documents += 1

                    if page_has_new_documents:
                        stale_pages = 0
                    else:
                        stale_pages += 1

                    if not perform_full_archive_scan:
                        # Sorted DATE_DESC means old pages after two stale pages are almost certainly already processed.
                        if stale_pages >= 2:
                            logger.info("Stopping early at page %s after stale window", page_index)
                            stopped_early = True
                            break

                if perform_full_archive_scan and not stopped_early:
                    marker = OpsDocumentLog(
                        document_url="__insider_trading_full_archive_completed__",
                        module_name="insider_trading",
                        status="SUCCESS",
                    )
                    session.add(marker)
                    session.commit()

            logger.info(
                "Insider job finished. New=%s Failed=%s",
                processed_new_documents,
                failed_documents,
            )
    except Exception as e:
        logger.error(f"Job failed: {e}")

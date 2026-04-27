import logging
from sqlmodel import Session, select
from sqlalchemy import inspect, text
from app.core.database import engine, OpsDocumentLog
from app.scraper.client import LiferayClient, BET_BASE_URL, BET_NEWS_API_URL
from app.utils.pdf import download_and_parse_pdf
from app.features.insider_trading.processor import vibe_check, extract_insider_data
from app.features.insider_trading.models import InsiderTrade

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
                for page_index, page_payload in client.iterate_solr_pages(
                    context=context,
                    category="NEWS_NOT_BET",
                    query="*",
                    order_mode="DATE_DESC",
                ):
                    raw_links = client.extract_result_links(page_payload)
                    subpages = [url for url in raw_links if _is_announcement_subpage(url)]
                    if not subpages:
                        continue

                    page_has_new_documents = False

                    for subpage in subpages:
                        absolute_subpage = client.to_absolute_url(subpage)
                        try:
                            pdf_urls = client.get_pdf_urls_from_announcement_subpage(absolute_subpage)
                        except Exception as exc:
                            logger.warning("Failed to parse announcement subpage %s: %s", absolute_subpage, exc)
                            continue

                        for pdf_url in pdf_urls:
                            exists = session.exec(
                                select(OpsDocumentLog).where(OpsDocumentLog.document_url == pdf_url)
                            ).first()
                            if exists:
                                continue

                            page_has_new_documents = True

                            try:
                                md_text = download_and_parse_pdf(pdf_url)

                                if vibe_check(md_text):
                                    extraction = extract_insider_data(md_text)
                                    if extraction.is_insider_trading:
                                        if extraction.insider_trade is None:
                                            raise ValueError("Missing insider_trade payload for insider document.")

                                        missing_fields = extraction.insider_trade.missing_fields()
                                        trade_data = extraction.insider_trade.model_dump()
                                        trade_data["has_missing_fields"] = bool(missing_fields)
                                        trade = InsiderTrade(
                                            **trade_data,
                                            document_url=pdf_url,
                                        )
                                        session.add(trade)

                                        if missing_fields:
                                            logger.info(
                                                "Persisted partial extraction for %s with missing fields: %s",
                                                pdf_url,
                                                ", ".join(missing_fields),
                                            )
                                    else:
                                        logger.info(
                                            "LLM marked %s as non-insider with certainty %.2f. Reason: %s",
                                            pdf_url,
                                            extraction.certainty,
                                            extraction.non_insider_reason,
                                        )

                                log_entry = OpsDocumentLog(
                                    document_url=pdf_url,
                                    module_name="insider_trading",
                                    status="SUCCESS",
                                )
                                session.add(log_entry)
                                session.commit()
                                processed_new_documents += 1
                            except Exception as exc:
                                logger.error("Error processing %s: %s", pdf_url, exc)
                                log_entry = OpsDocumentLog(
                                    document_url=pdf_url,
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

                    # Sorted DATE_DESC means old pages after two stale pages are almost certainly already processed.
                    if stale_pages >= 2:
                        logger.info("Stopping early at page %s after stale window", page_index)
                        break

            logger.info(
                "Insider job finished. New=%s Failed=%s",
                processed_new_documents,
                failed_documents,
            )
    except Exception as e:
        logger.error(f"Job failed: {e}")

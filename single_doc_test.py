import json
import os
from typing import Optional

from scraper.client import LiferayClient, BET_BASE_URL, BET_NEWS_API_URL
from utils.pdf import download_and_parse_pdf
from features.insider_trading.processor import extract_insider_data, vibe_check

PAGE_NUMBER = 29
ROW_NUMBER = 20
OVERWRITE_PDF = "https://bet.hu/newkibdata/129445207/ANY260424ER01H.pdf"



def fetch_api_page_links(page_number: int) -> list[str]:
    page_index = max(0, page_number - 1)

    with LiferayClient(BET_BASE_URL) as client:
        context = client.get_solr_search_context(BET_NEWS_API_URL)
        page_payload = client.search_solr(
            context=context,
            category="NEWS_NOT_BET",
            query="*",
            order_mode="DATE_DESC",
            page_index=page_index,
        )

        links = client.extract_result_links(page_payload)
        return [client.to_absolute_url(link) for link in links]


def fetch_pdf_from_row(page_links: list[str], row_number: int) -> Optional[str]:
    row_index = max(0, row_number - 1)
    if len(page_links) <= row_index:
        return None

    row_url = page_links[row_index]
    print(f"Using row {row_number} announcement page: {row_url}")

    with LiferayClient(BET_BASE_URL) as client:
        pdf_urls = client.get_pdf_urls_from_announcement_subpage(row_url)

    return pdf_urls[0] if pdf_urls else None


def main() -> int:
    if 'OVERWRITE_PDF' in globals():
        print(f"Using overwrite PDF URL: {OVERWRITE_PDF}") # type: ignore  # noqa: F821
        pdf_url = OVERWRITE_PDF # type: ignore  # noqa: F821
    else:
            
        print(f"Fetching page {PAGE_NUMBER} from the search API...")

        try:
            links = fetch_api_page_links(PAGE_NUMBER)
        except Exception as exc:
            print(f"Failed to fetch page {PAGE_NUMBER}: {exc}")
            return 1

        if not links:
            print(f"No results found on page {PAGE_NUMBER}.")
            return 1

        pdf_url = fetch_pdf_from_row(links, ROW_NUMBER)
        if not pdf_url:
            print(f"Could not find a PDF URL for row {ROW_NUMBER}.")
            return 1

    print(f"Downloading and parsing PDF: {pdf_url}")
    try:
        markdown_text = download_and_parse_pdf(pdf_url)
    except Exception as exc:
        print(f"Failed to download or parse PDF: {exc}")
        return 1

    project_root = os.path.dirname(os.path.abspath(__file__))
    tmp_dir = os.path.join(project_root, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    markdown_path = os.path.join(tmp_dir, "extracted_pdf.md")
    model_path = os.path.join(tmp_dir, "extracted_model.json")

    with open(markdown_path, "w", encoding="utf-8") as markdown_file:
        markdown_file.write(markdown_text)

    print(f"Saved extracted markdown to: {markdown_path}")
    if not vibe_check(markdown_text):
        print("Vibe check failed: document does not look like EU MAR Article 19 insider trading content.")
        return 1

    print("Sending parsed PDF text to the LLM extraction schema...")
    try:
        result = extract_insider_data(markdown_text)
    except Exception as exc:
        print(f"LLM extraction failed: {exc}")
        return 1

    if hasattr(result, "model_dump"):
        model_data = result.model_dump(mode="json")
    else:
        model_data = {"result": str(result)}

    with open(model_path, "w", encoding="utf-8") as model_file:
        json.dump(model_data, model_file, indent=2, ensure_ascii=False)

    print("\n=== Extraction Result ===")
    print(f"Markdown saved to: {markdown_path}")
    print(f"Model JSON saved to: {model_path}")
    print(json.dumps(model_data, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Standalone BET probe script.

Flow:
1) Start session + extract CSRF/search endpoint from /kereso page.
2) Request JSON pages for all announcements (NEWS_NOT_BET) with query="*".
3) Parse announcement subpage URLs.
4) Parse PDF URLs from each announcement subpage.

Usage examples:
- python bet_scraper_test.py --max-pages 3
- python bet_scraper_test.py --max-pages 0  # 0 means no limit (all pages)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.core.config import settings
from app.scraper.client import LiferayClient


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe BET Solr flow and extract announcement PDF URLs")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=3,
        help="How many Solr pages to crawl. Use 0 for no limit (all pages).",
    )
    parser.add_argument(
        "--max-subpages",
        type=int,
        default=40,
        help="How many announcement subpages to open for PDF extraction.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("probe_results.json"),
        help="Output JSON file path.",
    )
    args = parser.parse_args()

    page_limit = None if args.max_pages == 0 else max(1, args.max_pages)
    max_subpages = max(1, args.max_subpages)

    with LiferayClient(
        settings.BET_BASE_URL,
        min_delay_seconds=1.2,
        max_delay_seconds=3.0,
    ) as client:
        context = client.get_solr_search_context(settings.BET_NEWS_API_URL)

        print("Session established")
        print(f"- csrf token: {context.csrf_token}")
        print(f"- search url: {context.search_url}")
        print(f"- suggest url: {context.suggest_url}")
        print(f"- facets: {context.facets}")

        subpage_urls: list[str] = client.collect_announcement_subpage_urls(
            context=context,
            category="NEWS_NOT_BET",
            query="*",
            order_mode="DATE_DESC",
            page_limit=page_limit,
        )

        print(f"Found {len(subpage_urls)} announcement subpage URLs")

        scraped_subpages = []
        all_pdf_urls: list[str] = []
        seen_pdf_urls: set[str] = set()

        for subpage_url in subpage_urls[:max_subpages]:
            pdf_urls = client.get_pdf_urls_from_announcement_subpage(subpage_url)
            unique_pdf_urls = []
            for pdf_url in pdf_urls:
                if pdf_url in seen_pdf_urls:
                    continue
                seen_pdf_urls.add(pdf_url)
                unique_pdf_urls.append(pdf_url)
                all_pdf_urls.append(pdf_url)

            scraped_subpages.append(
                {
                    "subpage_url": subpage_url,
                    "pdf_urls": unique_pdf_urls,
                }
            )

        print(f"Collected {len(all_pdf_urls)} unique PDF URLs")
        for pdf_url in all_pdf_urls[:20]:
            print(f"PDF: {pdf_url}")

        output = {
            "search_context": {
                "source_page_url": context.source_page_url,
                "csrf_token": context.csrf_token,
                "search_url": context.search_url,
                "suggest_url": context.suggest_url,
                "facets": context.facets,
            },
            "total_subpages_found": len(subpage_urls),
            "subpages_processed": len(scraped_subpages),
            "unique_pdf_url_count": len(all_pdf_urls),
            "subpages": scraped_subpages,
        }

        args.out.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

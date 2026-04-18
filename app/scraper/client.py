import json
import random
import re
import time
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
DEFAULT_FACETS = [
    "bet_date",
    "bet_type",
    "bet_issuer_f",
    "bet_tag",
    "newkib_subjectGroup",
    "newkib_newssubject",
]


@dataclass(frozen=True)
class SolrSearchContext:
    source_page_url: str
    csrf_token: str
    search_url: str
    suggest_url: Optional[str]
    facets: list[str]


class LiferayClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = 30.0,
        min_delay_seconds: float = 1.0,
        max_delay_seconds: float = 2.5,
        user_agent: str = DEFAULT_USER_AGENT,
        client: Optional[httpx.Client] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.csrf_token: Optional[str] = None
        self.min_delay_seconds = max(0.0, min_delay_seconds)
        self.max_delay_seconds = max(self.min_delay_seconds, max_delay_seconds)
        self._owns_client = client is None

        if client is None:
            self.client = httpx.Client(
                base_url=self.base_url,
                timeout=timeout_seconds,
                follow_redirects=True,
                headers={
                    "User-Agent": user_agent,
                    "Accept-Language": "hu-HU,hu;q=0.9,en;q=0.8",
                },
            )
        else:
            self.client = client

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def close(self):
        if self._owns_client:
            self.client.close()

    def _sleep_polite(self):
        if self.max_delay_seconds <= 0:
            return
        time.sleep(random.uniform(self.min_delay_seconds, self.max_delay_seconds))

    def _to_absolute_url(self, url_or_path: str) -> str:
        if url_or_path.startswith("http://") or url_or_path.startswith("https://"):
            return url_or_path
        return urljoin(f"{self.base_url}/", url_or_path)

    def to_absolute_url(self, url_or_path: str) -> str:
        return self._to_absolute_url(url_or_path)

    @staticmethod
    def _extract_js_string(script_text: str, variable_name: str) -> Optional[str]:
        match = re.search(rf'var\s+{re.escape(variable_name)}\s*=\s*"([^"]+)"\s*;', script_text)
        if not match:
            return None
        return match.group(1).replace("\\/", "/")

    @staticmethod
    def _extract_js_string_list(script_text: str, variable_name: str) -> list[str]:
        match = re.search(
            rf"var\s+{re.escape(variable_name)}\s*=\s*\[(.*?)\]\s*;",
            script_text,
            flags=re.DOTALL,
        )
        if not match:
            return []

        raw_array = f"[{match.group(1)}]".replace("'", '"')
        try:
            data = json.loads(raw_array)
            return [value for value in data if isinstance(value, str)]
        except json.JSONDecodeError:
            values = []
            for token in match.group(1).split(","):
                token = token.strip().strip('"').strip("'")
                if token:
                    values.append(token)
            return values

    def fetch_html(self, url_or_path: str) -> str:
        self._sleep_polite()
        response = self.client.get(url_or_path)
        response.raise_for_status()
        return response.text

    def get_solr_search_context(self, search_page_url: str) -> SolrSearchContext:
        html = self.fetch_html(search_page_url)
        soup = BeautifulSoup(html, "html.parser")

        csrf_meta = soup.find("meta", attrs={"name": "_csrf"})
        csrf_token = (csrf_meta or {}).get("content") if csrf_meta else None
        if not csrf_token:
            raise RuntimeError("Could not find _csrf token on Liferay search page")

        search_url: Optional[str] = None
        suggest_url: Optional[str] = None
        facets: list[str] = []

        for script in soup.find_all("script"):
            script_text = script.get_text(" ", strip=False)
            if "$risearch" not in script_text:
                continue

            extracted_search = self._extract_js_string(script_text, "searchUrl")
            if extracted_search:
                search_url = self._to_absolute_url(extracted_search)
                extracted_suggest = self._extract_js_string(script_text, "suggestUrl")
                suggest_url = self._to_absolute_url(extracted_suggest) if extracted_suggest else None
                facets = self._extract_js_string_list(script_text, "facets")
                break

        if not search_url:
            fallback = re.search(r'var\s+searchUrl\s*=\s*"([^"]+\$risearch)"\s*;', html)
            if fallback:
                search_url = self._to_absolute_url(fallback.group(1).replace("\\/", "/"))

        if not search_url:
            raise RuntimeError("Could not find Liferay Solr searchUrl on search page")

        if not facets:
            facets = list(DEFAULT_FACETS)

        self.csrf_token = csrf_token
        return SolrSearchContext(
            source_page_url=self._to_absolute_url(search_page_url),
            csrf_token=csrf_token,
            search_url=search_url,
            suggest_url=suggest_url,
            facets=facets,
        )

    def search_solr(
        self,
        context: SolrSearchContext,
        query: str = "*",
        category: Optional[str] = None,
        page_index: int = 0,
        order_mode: str = "DATE_DESC",
        dd_params: Optional[list[dict[str, str]]] = None,
        facets: Optional[list[str]] = None,
        content_permission: Optional[list[str]] = None,
        date_from: Optional[str] = None,
        date_till: Optional[str] = None,
        archive_date_mode: Optional[str] = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "query": query or "*",
            "facets": facets if facets is not None else context.facets,
            "ddParams": dd_params or [],
            "pageIndex": page_index,
            "orderMode": order_mode,
            "contentPermission": content_permission or ["READ"],
        }

        if category:
            payload["category"] = category
        if date_from:
            payload["dateFrom"] = date_from
        if date_till:
            payload["dateTill"] = date_till
        if archive_date_mode:
            payload["archiveDateMode"] = archive_date_mode

        endpoint = f"{context.search_url}?_csrf={context.csrf_token}"
        origin = f"{httpx.URL(self.base_url).scheme}://{httpx.URL(self.base_url).host}"
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/json; charset=UTF-8",
            "Origin": origin,
            "Referer": context.source_page_url,
            "X-Requested-With": "XMLHttpRequest",
        }

        self._sleep_polite()
        response = self.client.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    def iterate_solr_pages(
        self,
        context: SolrSearchContext,
        category: str,
        query: str = "*",
        order_mode: str = "DATE_DESC",
        page_limit: Optional[int] = None,
    ):
        page_index = 0
        seen_page_count: Optional[int] = None

        while True:
            result = self.search_solr(
                context=context,
                query=query,
                category=category,
                page_index=page_index,
                order_mode=order_mode,
            )
            yield page_index, result

            if seen_page_count is None:
                page_count_raw = result.get("pageCount")
                seen_page_count = page_count_raw if isinstance(page_count_raw, int) else 0

            page_index += 1
            if page_limit is not None and page_index >= page_limit:
                break
            if seen_page_count is not None and page_index >= seen_page_count:
                break

    @staticmethod
    def extract_result_links(result_payload: dict[str, Any]) -> list[str]:
        links: list[str] = []
        for item in result_payload.get("items", []):
            fragment = item.get("data")
            if not isinstance(fragment, str) or not fragment.strip():
                continue
            soup = BeautifulSoup(fragment, "html.parser")
            for anchor in soup.find_all("a", href=True):
                href = anchor["href"].strip()
                if href:
                    links.append(href)
        return links

    def collect_announcement_subpage_urls(
        self,
        context: SolrSearchContext,
        category: str,
        query: str = "*",
        order_mode: str = "DATE_DESC",
        page_limit: Optional[int] = None,
    ) -> list[str]:
        seen: set[str] = set()
        ordered_urls: list[str] = []

        for _, page in self.iterate_solr_pages(
            context=context,
            category=category,
            query=query,
            order_mode=order_mode,
            page_limit=page_limit,
        ):
            for href in self.extract_result_links(page):
                absolute_url = self._to_absolute_url(href)
                if absolute_url in seen:
                    continue

                seen.add(absolute_url)
                ordered_urls.append(absolute_url)

        return ordered_urls

    def extract_pdf_urls_from_subpage_html(self, subpage_html: str) -> list[str]:
        soup = BeautifulSoup(subpage_html, "html.parser")

        containers = soup.select("div.AttachmentPortlet")
        if not containers:
            containers = [soup]

        pdf_urls: list[str] = []
        seen: set[str] = set()

        for container in containers:
            for anchor in container.find_all("a", href=True):
                href = anchor["href"].strip()
                if not href:
                    continue

                href_lower = href.lower()
                if ".pdf" not in href_lower:
                    continue

                absolute_url = self._to_absolute_url(href)
                if absolute_url in seen:
                    continue
                seen.add(absolute_url)
                pdf_urls.append(absolute_url)

        return pdf_urls

    def get_pdf_urls_from_announcement_subpage(self, subpage_url: str) -> list[str]:
        html = self.fetch_html(subpage_url)
        return self.extract_pdf_urls_from_subpage_html(html)

    def authenticate(self, target_url: str):
        context = self.get_solr_search_context(target_url)
        self.csrf_token = context.csrf_token

    def get_news(self, api_path: str, payload: dict):
        if not self.csrf_token:
            raise RuntimeError("Not authenticated")

        headers = {
            "X-SECURITY": self.csrf_token,
            "Content-Type": "application/json; charset=UTF-8",
        }
        self._sleep_polite()
        response = self.client.post(api_path, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

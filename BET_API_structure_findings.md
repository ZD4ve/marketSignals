# BET Liferay Scraping Findings (Insider/Announcement Pipeline)

Date: 2026-04-18
Target: https://bet.hu/kereso?category=NEWS_NOT_BET

## Executive Summary
The BET search page is powered by a Liferay/Solr endpoint that requires a fresh browser-like session and a per-page CSRF token. The flow is:

1. GET search page to establish cookies (`JSESSIONID`) and read dynamic config.
2. Extract `_csrf` and dynamic Solr endpoint (`$risearch`) from page HTML.
3. POST JSON to the `$risearch` endpoint with `query="*"` and `category="NEWS_NOT_BET"`.
4. Parse announcement subpage URLs from returned `items[].data` HTML fragments.
5. Open each announcement subpage and extract attachment PDF links, primarily under `/newkibdata/...pdf`.

This works reliably without keyword filtering.

## Session and Token Mechanics

### Required bootstrap request
- Request URL: `https://bet.hu/kereso?category=NEWS_NOT_BET`
- Purpose:
  - Creates session cookie (`JSESSIONID`).
  - Exposes CSRF token in HTML meta:
    - `<meta name="_csrf" content="...">`
  - Exposes dynamic Solr URLs in inline script:
    - `var searchUrl = "/kereso/$rspid.../$risearch";`
    - `var suggestUrl = "/kereso/$rspid.../$risuggest";`

### Why old curl sessions fail
The copied curl example used stale values for both:
- cookie (`JSESSIONID=...`)
- `_csrf` query parameter

These are session-bound and must be re-collected from a fresh GET.

## Correct JSON Search Request

### Endpoint shape
- `https://bet.hu/kereso/$rspid.../$risearch?_csrf=<fresh_csrf>`

### Method
- `POST`

### Effective headers
- `Accept: application/json, text/javascript, */*; q=0.01`
- `Content-Type: application/json; charset=UTF-8`
- `Origin: https://bet.hu`
- `Referer: https://bet.hu/kereso?category=NEWS_NOT_BET`
- `X-Requested-With: XMLHttpRequest` (optional but browser-like)
- Browser-like `User-Agent`

### Body (unfiltered, all announcements)
```json
{
  "query": "*",
  "facets": [
    "bet_date",
    "bet_type",
    "bet_issuer_f",
    "bet_tag",
    "newkib_subjectGroup",
    "newkib_newssubject"
  ],
  "ddParams": [],
  "pageIndex": 0,
  "orderMode": "DATE_DESC",
  "category": "NEWS_NOT_BET",
  "contentPermission": ["READ"]
}
```

### Response structure
```json
{
  "items": [
    {"data": "<a href=\"/site/newkib/...\">...</a>"},
    ...
  ],
  "numFound": 117500,
  "pageCount": 4700,
  "facets": {...}
}
```

- `items[].data` is HTML, not plain JSON objects.
- The announcement URL is found inside anchor tags in this HTML fragment.

## Announcement -> PDF URL Resolution

### Announcement subpage URL pattern
- `/site/newkib/...`

### Attachment PDF location
On announcement pages, PDFs are rendered in the `AttachmentPortlet` section (`Csatolt dokumentumok`):
- Typical URL pattern: `/newkibdata/<id>/<file>.pdf`
- Some pages may include `/pfile/file?path=...` links; these are often general site documents and should not be treated as the primary announcement attachment unless needed.

### Verified end-to-end sample
- Subpage: `https://bet.hu/site/newkib/hu/2026.04./OPUS_GLOBAL_Nyrt._-_Sajat_reszveny_tranzakcio_129441665`
- Attachment PDF: `https://bet.hu/newkibdata/129441665/OPUS_r%C3%A9szv%C3%A9ny%20v%C3%A1s%C3%A1rl%C3%A1s_20260417_HU.pdf`
- Download verified (`Content-Type: application/pdf`, `%PDF-1.7` magic bytes).

## Anti-Rate-Limit / Safety Practices
To avoid bans and throttling:
- Keep one persistent session (`httpx.Client`) instead of reconnecting per request.
- Add random delay between requests (e.g., 1.2s-3.0s).
- Use realistic browser headers.
- Avoid aggressive parallelism; crawl sequentially or with very low concurrency.
- Re-bootstrap session/token periodically (or on 403/419-like failures).

## Implemented in Codebase
- Generic Liferay/Solr mechanics integrated in scraper client:
  - Session + CSRF extraction
  - Dynamic `$risearch` discovery
  - Unfiltered pagination helpers
  - Announcement subpage extraction
  - PDF URL extraction from attachment blocks

- Insider task orchestration integrated to:
  - Pull announcement pages from unfiltered `NEWS_NOT_BET`
  - Resolve PDF URLs from each announcement subpage
  - Continue with existing PDF parse + vibe check + LLM extraction + DB writes

## Throwaway Probe Script
Created script:
- `bet_scraper_test.py`

It performs exactly:
1. Session setup and token extraction.
2. Right Solr request for announcement JSON pages.
3. Parsing announcement subpage URLs.
4. Parsing attached PDF URLs from each subpage.

Default behavior is polite (random delays, limited page/subpage count by CLI). It can be switched to full crawl by using `--max-pages 0`.

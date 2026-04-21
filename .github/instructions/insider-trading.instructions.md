---
description: "Context and rules for modifying or extending the Insider Trading module. Use this when working on insider trading logic."
applyTo: "app/features/insider_trading/**"
---

# Insider Trading Module

## Domain Context
This module is responsible for fetching, parsing, and extracting EU MAR Article 19 insider trading information from the Budapest Stock Exchange (BET).

## Components
- **`models.py`**: Defines the `InsiderTrade` SQLModel which maps to the `insider_trades` table in PostgreSQL. Used for persistence.
- **`schemas.py`**: Defines the `EUMarArticle19` Pydantic model. This is strictly used by `instructor` and the selected OpenRouter LLM to enforce the JSON schema during extraction.
- **`processor.py`**: Contains the core business logic. 
  - `vibe_check(markdown_text)`: A fast regex heuristic to verify if a downloaded document is actually an insider trading report before sending it to the LLM.
  - `extract_insider_data(markdown_text)`: Passes the verified Markdown to the configured OpenRouter model to extract the `EUMarArticle19` schema.
- **`tasks.py`**: The APScheduler job (`fetch_insider_news_job`). This orchestrates the flow:
  1. Requests URLs from the Liferay hidden API (via `app/scraper/client.py`).
  2. Checks `ops_document_log` to avoid reprocessing the same URL.
  3. Downloads and converts PDF to Markdown (via `app/utils/pdf.py`).
  4. Runs `vibe_check`.
  5. Extracts data via `extract_insider_data`.
  6. Saves to `insider_trades` and updates `ops_document_log`.

## Rules
1. **No Core Pollution**: Do not add insider-trading-specific logic to `app/core/` or `app/scraper/`.
2. **Schema Matching**: If changing a field, you MUST update both `models.py` (database) and `schemas.py` (LLM extraction) to keep them aligned.

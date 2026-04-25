# BET Automated Background Data Platform

## Overview
An extensible, highly modular, automated background data pipeline designed to scrape, process, and extract structured market signals from the Budapest Stock Exchange (BET). Currently, it specializes in extracting **EU MAR Article 19 Insider Trading** reports from dynamic PDFs using OpenRouter models and `instructor`. 

The system operates as a headless background processor driven by `APScheduler`, extracting and structuring unstructured data into a relational PostgreSQL database. Its Domain-Driven Design (DDD) architecture ensures the backend is completely decoupled, making it trivial to attach a FastAPI frontend or scale out to new data extraction features (e.g., Sentiment Analysis, Technical Indicators).

## Architecture Highlights
- **Domain-Driven Design (Feature-based structure):** New data extraction modules can be added without modifying existing domains.
- **LLM-Enforced Extraction:** Uses `instructor` alongside Pydantic schemas to strictly type LLM outputs into relational datastores.
- **Global Operation Tracking:** A core `ops_document_log` registry ensures multiple data modules do not redundantly process or download the same documents.
- **Dockerized & Scalable:** Fully managed via Docker Compose leveraging a local PostgreSQL instance for concurrency-safe task execution.

## Core Stack
- **Languages/Frameworks:** Python 3.11, SQLModel, Pydantic, APScheduler.
- **Scraping:** HTTPX, BeautifulSoup4, PyMuPDF4LLM.
- **AI/LLM:** OpenAI Client (via OpenRouter), Instructor.
- **Infrastructure:** Docker, Docker Compose, PostgreSQL.

## Local Development (Dev Container)

1. **Clone the repository:**
   ```bash
   git clone <repo_url>
   cd <repo_directory>
   ```

2. **Configure Environment:**
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

   Keep the local `.env` minimal for devcontainer use:
   ```dotenv
   LLM_API_KEY=replace_with_openrouter_api_key
   LLM_MODEL=anthropic/claude-3.5-sonnet
   POSTGRES_PASSWORD=dev_postgres_password
   ```

   Notes:
   - `POSTGRES_PASSWORD` must exist locally so compose interpolation succeeds when VS Code starts the dev stack.
   - The dev stack itself pins local DB credentials in `.devcontainer/docker-compose.dev.yml`.
   - You do not need to set `POSTGRES_USER`, `POSTGRES_DB`, `POSTGRES_HOST`, or `POSTGRES_PORT` in local `.env` for devcontainer workflow.

3. **Open in Dev Container (recommended):**
   - Open the repository in VS Code.
   - Run `Dev Containers: Reopen in Container`.
   - VS Code uses `.devcontainer/devcontainer.json` with `docker-compose.yml` plus `.devcontainer/docker-compose.dev.yml`.

4. **Optional: Start the same dev stack from CLI:**
   ```bash
   docker compose -f docker-compose.yml -f .devcontainer/docker-compose.dev.yml up -d --build
   ```

## Portainer Deployment (Git Stack)

Use `docker-compose.yml` as the stack file in Portainer Git deployment.

Required Portainer stack environment variables:
- `LLM_API_KEY`
- `POSTGRES_PASSWORD`

Optional overrides:
- `LLM_BASE_URL`
- `LLM_MODEL`
- `POSTGRES_USER`
- `POSTGRES_DB`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

Notes:
- `docker-compose.yml` is deployment-oriented (no source bind mount).
- Dev-only bind mounts and local conveniences are defined in `.devcontainer/docker-compose.dev.yml`.
- `POSTGRES_PASSWORD` should be a strong deployment secret in Portainer (do not use local dev value).

Recommended Portainer flow:
1. Create a stack from your Git repository.
2. Set compose path to `docker-compose.yml`.
3. Define stack environment variables (required + optional overrides).
4. Deploy the stack.

## Development & Extensibility
This project relies closely on strict architectural rules outlined in `.github/copilot-instructions.md`. When developing new features, create a completely isolated folder inside `app/features/` containing its respective DB models, extraction schemas, and pipeline tasks.

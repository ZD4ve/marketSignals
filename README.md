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

## Getting Started

1. **Clone the repository:**
   ```bash
   git clone <repo_url>
   cd <repo_directory>
   ```

2. **Configure Environment:**
   Copy the example environment file and fill in your API keys (e.g., OpenRouter API key).
   ```bash
   cp .env.example .env
   ```

3. **Deploy with Docker Compose:**
   ```bash
   docker-compose up -d --build
   ```

## Development & Extensibility
This project relies closely on strict architectural rules outlined in `.github/copilot-instructions.md`. When developing new features, create a completely isolated folder inside `app/features/` containing its respective DB models, extraction schemas, and pipeline tasks.

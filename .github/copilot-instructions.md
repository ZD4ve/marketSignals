# GitHub Copilot Instructions - BET Automated Background Data Platform

## Architecture Overview
This project strictly follows Domain-Driven Design (DDD) specifically modularized by features. 
Do NOT mix domains or pollute the core logic with feature-specific business logic. This prepares the backend for a highly scalable FastAPI frontend later.

### Directory Structure Rules:
- `app/core/`: Contains ONLY shared scaffolding (Database Engine, LLM Client initialization, Global Config).
- `app/scraper/`: Contains ONLY the generic Liferay authenticated HTTPX client. Do not put specific targeted scraping logic here.
- `app/utils/`: Contains generic utilities (e.g. PDF to Markdown parser).
- `app/features/<feature_name>/`: ALL feature-specific code goes here. 
  - `models.py`: PostgreSQL tables via SQLModel.
  - `schemas.py`: Pydantic validation and LLM extraction schemas.
  - `processor.py`: Business logic, filtering, parsing, LLM execution.
  - `tasks.py`: APScheduler job orchestrations (the entry point for the module).

### General Rules:
- **Database:** Use `SQLModel` for all database interactions.
- **Extraction:** Use `instructor` with `openai` pointing to OpenRouter to enforce structured JSON output.
- **Isolation:** Features should NEVER import from other features, only from `app/core/` and other shared utilities.

### Feature-Specific Instructions
Additional context for AI agents is provided in the `.github/instructions/` directory:
- Working on Insider Trading: See `.github/instructions/insider-trading.instructions.md`
- Creating a New Module: See `.github/instructions/new-module.instructions.md`

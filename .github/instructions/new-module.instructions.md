---
description: "Instructions and architectural rules for scaffolding a new feature module in the BET data platform. Use this when adding a new data extraction feature, watcher, or module."
---

# Creating a New Feature Module

## Architectural Philosophy (Domain-Driven Design)
The BET Automated Background Data Platform uses feature-based isolation. When creating a new feature (e.g., `technical_analysis`, `notifications`), it MUST be completely isolated inside its own folder under `app/features/<feature_name>/`.

## Step-by-Step Scaffolding

1. **Create the Folder Structure**:
   Create a new directory: `app/features/<feature_name>/`

2. **Define the Database Model (`models.py`)**:
   - Create a `SQLModel` class for the specific data you are saving.
   - Example: `class TechIndicator(SQLModel, table=True):`
   - Store it in `app/features/<feature_name>/models.py`.

3. **Define the LLM Extraction Schema (`schemas.py`)**:
   - If the module uses an LLM to extract data, create a strictly typed Pydantic `BaseModel`.
   - Ensure each field has a clear `Field(..., description="...")` to guide the OpenRouter model.
   - Store it in `app/features/<feature_name>/schemas.py`.

4. **Write the Business Logic (`processor.py`)**:
   - Include any pre-filtering/vibe-checking logic (e.g., regex checks) to avoid expensive LLM calls if the document doesn't match the new domain.
   - Add the LLM extraction function using `instructor` and the schema.

5. **Create the Scheduler Task (`tasks.py`)**:
   - Write the orchestrator function.
   - **Crucial**: Always check the global `ops_document_log` table (from `app/core/database.py`) before processing a URL/document to ensure it hasn't been handled already.
   - If processed successfully, log it to `ops_document_log` with `module_name="<feature_name>"`.

6. **Register the Task (`app/main.py`)**:
   - Import your new task into `app/main.py`.
   - Register it with the `APScheduler` instance.

## Hard Rules
- **Do not import from other features**: `app/features/a/` cannot import from `app/features/b/`.
- **Use shared utilities**: If you need to download a PDF or make an authenticated Liferay request, use `app/utils/pdf.py` and `app/scraper/client.py`. If those utilities lack functionality, upgrade the utilities generically, do not build custom scrapers inside your feature folder.

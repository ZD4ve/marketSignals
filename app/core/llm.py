import instructor
from openai import OpenAI
from app.core.config import settings

# Initialize the LLM client using environment-configurable endpoint and key
llm_api_key = settings.LLM_API_KEY
openai_kwargs = {
    "base_url": settings.LLM_BASE_URL,
    "default_headers": {
        #TODO: Add referer header with the URL of the app when deployed to production
        #"HTTP-Referer": APP URL,
        "X-Title": "marketSignals",
    }
}
if llm_api_key:
    openai_kwargs["api_key"] = llm_api_key

client = instructor.from_openai(
    OpenAI(**openai_kwargs),
    mode=instructor.Mode.TOOLS,
)


def get_openrouter_provider_body(require_parameters: bool = True) -> dict:
    return {"provider": {"require_parameters": require_parameters}}


def get_llm_client():
    return client

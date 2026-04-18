import instructor
from openai import OpenAI
from app.core.config import settings

# Initialize OpenAI client pointed at OpenRouter with instructor for structured outputs
client = instructor.from_openai(
    OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API_KEY,
    ),
    mode=instructor.Mode.JSON
)

def get_llm_client():
    return client

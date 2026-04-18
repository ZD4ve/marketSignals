import re
from app.core.llm import get_llm_client
from app.features.insider_trading.schemas import EUMarArticle19

def vibe_check(markdown_text: str) -> bool:
    keywords = [r"bennfentes", r"vezet[őo] állású", r"Article 19", r"19\. cikk"]
    pattern = re.compile("|".join(keywords), re.IGNORECASE)
    return bool(pattern.search(markdown_text))

def extract_insider_data(markdown_text: str) -> EUMarArticle19:
    client = get_llm_client()
    
    from app.core.config import settings
    
    response = client.chat.completions.create(
        model=settings.OPENROUTER_MODEL,
        messages=[
            {
                "role": "user",
                "content": f"Extract the EU MAR Article 19 insider trading information from this document:\n\n{markdown_text}"
            }
        ],
        response_model=EUMarArticle19,
    )
    return response

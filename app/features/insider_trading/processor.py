import re
from app.core.llm import get_llm_client, get_openrouter_provider_body
from app.features.insider_trading.schemas import EUMarArticle19

def vibe_check(markdown_text: str) -> bool:
    keywords = [
        r"bennfentes", 
        r"vezet[őo] állású", 
        r"vezetői feladatokat ellátó", 
        r"Article 19", 
        r"19\. cikk",
        r"596/2014", 
        r"piaci visszaélésekről"
    ]
    pattern = re.compile("|".join(keywords), re.IGNORECASE)
    #TODO: add lenght check to avoid processing very long documents that are unlikely to be relevant
    return bool(pattern.search(markdown_text))

def extract_insider_data(markdown_text: str) -> EUMarArticle19:
    client = get_llm_client()
    
    from app.core.config import settings
    
    response = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {
                "role": "user",
                "content": f"Extract the EU MAR Article 19 insider trading information from this document:\n\n{markdown_text}"
            }
        ],
        extra_body=get_openrouter_provider_body(require_parameters=True),
        response_model=EUMarArticle19,
    )
    return response

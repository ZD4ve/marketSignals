import re
from app.core.llm import get_llm_client, get_openrouter_provider_body
from app.features.insider_trading.schemas import InsiderExtractionResult

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
    max_length = 20_000
    if len(markdown_text) > max_length:
        return False

    pattern = re.compile("|".join(keywords), re.IGNORECASE)
    return bool(pattern.search(markdown_text))

def extract_insider_data(markdown_text: str) -> InsiderExtractionResult:
    client = get_llm_client()

    from app.core.config import settings

    prompt = (
        "Decide whether this document is an EU MAR Article 19 PDMR dealing notification and return JSON that matches the schema.\n"
        "Rules:\n"
        "0) In this system, 'insider trading' means the mandatory Article 19 disclosure format, not an accusation of illegal market abuse.\n"
        "   Routine executive buy/sell disclosures are insider-trading documents for extraction."
        "1) The document have been pre-processed already, so it is 99%% likely to be an Article 19 disclosure.\n"
        "2) Set is_insider_trading=false only when you are absolutely certain, and then set certainty=1.0.\n"
        "3) If the document has any of the Article 19 table/fields (PDMR name, position, issuer, LEI, ISIN, transaction type/date/place), set is_insider_trading=true.\n"
        "4) If there is any uncertainty, set is_insider_trading=true and provide insider_trade.\n"
        "5) A sell transaction is still insider_trading=true when it is an Article 19 disclosure.\n"
        "6) If some fields are missing from the document, still extract the fields that are present and leave the rest null.\n"
        "7) For non-insider verdicts, include non_insider_reason and evidence_snippets copied from the document.\n\n"
        f"Document:\n{markdown_text}"
    )

    response = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        extra_body=get_openrouter_provider_body(require_parameters=True),
        response_model=InsiderExtractionResult,
    )
    return response

import pymupdf4llm
import httpx
import tempfile
import os

def download_and_parse_pdf(url: str) -> str:
    with httpx.Client() as client:
        response = client.get(url)
        response.raise_for_status()
        
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(response.content)
        tmp_path = tmp.name
        
    try:
        md_text = pymupdf4llm.to_markdown(tmp_path)
        return md_text
    finally:
        os.remove(tmp_path)

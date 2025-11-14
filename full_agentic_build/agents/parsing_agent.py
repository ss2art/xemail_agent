from bs4 import BeautifulSoup
import re

def extract_text(raw_email: str) -> str:
    if not raw_email:
        return ""
    soup = BeautifulSoup(raw_email, "html.parser")
    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:50000]

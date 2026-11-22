"""Rule-based checks used by the analyzer. Standard library only, so they can be tested
without loading the embedding model."""
import re

TAG = re.compile(r"<[^<>]+>")
_INDIC = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")


def strip_tags(text: str) -> str:
    """Remove inline markup such as <g id="1"> or <x id="2"/> (from XLIFF files)."""
    return re.sub(r"\s+", " ", TAG.sub(" ", text)).strip()


def normalize_digits(text: str) -> str:
    """Arabic-Indic (٠-٩) and Persian (۰-۹) digits to 0-9."""
    return text.translate(_INDIC)


def arabic_ratio(text: str) -> float:
    text = strip_tags(text)
    if not text:
        return 0.0
    arabic_chars = len(re.findall(r"[؀-ۿ]", text))
    letters = len(re.findall(r"[A-Za-z؀-ۿ]", text))
    return arabic_chars / letters if letters else 0.0


def length_ratio(source: str, target: str) -> float:
    return len(strip_tags(target)) / max(len(strip_tags(source)), 1)


def extract_placeholders(text):
    patterns = [r"\{[^{}]+\}", r"%[sdif]", r"\$\{[^{}]+\}", r"<[^<>]+>"]
    out = []
    for p in patterns:
        out.extend(re.findall(p, text))
    return sorted(out)


def extract_numbers(text):
    return sorted(re.findall(r"\d+(?:[.,]\d+)?", normalize_digits(strip_tags(text))))

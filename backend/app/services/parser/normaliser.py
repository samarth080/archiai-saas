import re

from app.services.parser.data.synonyms import NUMBER_WORDS, SYNONYMS


def _replace_phrase(text: str, phrase: str, replacement: str) -> str:
    return re.sub(rf"\b{re.escape(phrase)}\b", replacement, text, flags=re.IGNORECASE)


def normalise(prompt: str) -> str:
    """Lowercase, canonicalise known phrases, expand number words, and collapse whitespace."""
    text = prompt.lower().strip().replace("-", " ")

    for phrase, canonical in sorted(SYNONYMS.items(), key=lambda item: -len(item[0])):
        text = _replace_phrase(text, phrase.replace("-", " "), canonical)

    for word, digit in sorted(NUMBER_WORDS.items(), key=lambda item: -len(item[0])):
        text = _replace_phrase(text, word, str(digit))

    return re.sub(r"\s+", " ", text).strip()


def tokenize(prompt: str) -> list[str]:
    text = normalise(prompt)
    return re.findall(r"[a-z0-9_]+", text)


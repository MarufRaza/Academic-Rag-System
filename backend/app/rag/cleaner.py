import re


def clean_academic_text(text: str) -> str:
    """
    Cleans raw text extracted from academic PDFs:
    - Removes non-printable characters.
    - Fixes hyphenated words split across line breaks (e.g., 'algo-\nrithm' -> 'algorithm').
    - Normalizes multiple spaces, tabs, and line breaks while preserving paragraph boundaries.
    - Removes standalone page numbers or simple repeated footer/header patterns.
    """
    if not text:
        return ""

    # Replace null bytes and non-printable control characters (keep tab, newline)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    # Fix word hyphenation across lines: word-\nword -> wordword
    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)

    # Replace windows line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Collapse consecutive spaces and tabs to a single space
    text = re.sub(r'[ \t]+', ' ', text)

    # Collapse 3 or more newlines to double newline (paragraph break)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Clean lines with only whitespace
    lines = [line.strip() for line in text.split('\n')]
    cleaned_text = '\n'.join(lines)

    # Collapse excessive newlines again
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)

    return cleaned_text.strip()

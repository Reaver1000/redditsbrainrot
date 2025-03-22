# replacements.py

import re
import unicodedata
import inflect  # For number-to-words conversion
from unidecode import unidecode  # For Unicode transliteration

# Initialize inflect engine
p = inflect.engine()

# Dictionary for Unicode and mojibake replacements
replacements = {
    # Curly single quotes
    '‘': "'", '’': "'", '`': "'", '´': "'", '′': "'",
    # Curly double quotes
    '“': '"', '”': '"', '„': '"', '‟': '"', '″': '"',
    # Dashes and hyphens
    '–': '-', '—': '-', '−': '-', '‐': '-', '‑': '-',
    # Ellipsis
    '…': '...', '⋯': '...', '…': '...',
    # Other problematic characters
    'â': "'", 'â': "'", 'â': '"', 'â': '"', 'â': '-', 'â': '-', 'â¦': '...',
    '\ufeff': '',  # Remove BOM
}

# Dictionary for family abbreviations
family_abbreviations = {
    r'\bMIL\b': 'mother in law',
    r'\bSIL\b': 'sister in law',
    r'\bBIL\b': 'brother in law',
    r'\bFIL\b': 'father in law',
}

def sanitize_text(text):
    """Clean text for TTS and subtitles"""
    if not text:
        return ""

    # Normalize Unicode characters to decompose combined characters
    text = unicodedata.normalize('NFKD', text)
    
    # Replace specific Unicode characters and mojibake sequences
    for old, new in replacements.items():
        text = text.replace(old, new)

    # Replace contractions like "I'm" and "I’m" with "I am"
    text = re.sub(r"I'm", "I am", text, flags=re.IGNORECASE)
    text = re.sub(r"I’m", "I am", text, flags=re.IGNORECASE)

    # Custom case-insensitive replacements for phrases
    # Replace AITAH first, then AITA, then WIBTA
    text = re.sub(r'\bAITAH\b', 'Am I the Asshole', text, flags=re.IGNORECASE)
    text = re.sub(r'\bAITA\b', 'Am I the Asshole', text, flags=re.IGNORECASE)
    text = re.sub(r'\bWIBTA\b', 'Would I be the Asshole', text, flags=re.IGNORECASE)

    # Custom case-insensitive replacements for single letters (M and F)
    # Replace M/m with male and F/f with female in various contexts
    text = re.sub(r'\((\d+)([Ff])\)', r'\1 female', text)  # Replace (34f) or (34F) with (34 female)
    text = re.sub(r'\((\d+)([Mm])\)', r'\1 male', text)    # Replace (34m) or (34M) with (34 male)
    text = re.sub(r'\(([Ff])\)', r'female', text)          # Replace (F) or (f) with (female)
    text = re.sub(r'\(([Mm])\)', r'male', text)            # Replace (M) or (m) with (male)
    text = re.sub(r'(\d+)([Ff])', r'\1 female', text)        # Replace 27f or 27F with 27 female
    text = re.sub(r'(\d+)([Mm])', r'\1 male', text)          # Replace 30m or 30M with 30 male
    text = re.sub(r'\b([Ff])\b', 'female', text)             # Replace standalone F or f with female
    text = re.sub(r'\b([Mm])\b', 'male', text)               # Replace standalone M or m with male

    # Perform case-insensitive replacements for family abbreviations
    for abbrev, full_form in family_abbreviations.items():
        text = re.sub(abbrev, full_form, text, flags=re.IGNORECASE)

    # Remove TLDR (case-insensitive)
    text = re.sub(r'\bTLDR\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\btl;dr\b', '', text, flags=re.IGNORECASE)

    # Remove currency symbols ($, £, €)
    text = re.sub(r'[$£€]', '', text)

    # Convert numbers to words
    def number_to_words(match):
        number = match.group(0)
        try:
            return p.number_to_words(number)
        except:
            return number

    # Replace numbers with words
    text = re.sub(r'\b\d+\b', number_to_words, text)

    # Handle numbers followed by K or k (e.g., 10K → ten thousand)
    def handle_k_suffix(match):
        number = match.group(1)
        try:
            words = p.number_to_words(number)
            return f"{words} thousand"
        except:
            return match.group(0)

    text = re.sub(r'(\d+)[Kk]', handle_k_suffix, text)

    # Transliterate remaining Unicode characters to ASCII
    text = unidecode(text)

    # Remove control characters and non-printable Unicode
    cleaned = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)

    # Remove markdown formatting (bold/italic/links)
    cleaned = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', cleaned)  # Links
    cleaned = re.sub(r'(?<!\\)[\*_]{1,3}(.*?)(?<!\\)[\*_]{1,3}', r'\1', cleaned)  # Bold/italic
    
    # Remove blockquotes and code blocks
    cleaned = re.sub(r'^>.*$', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'`{3}.*?`{3}', '', cleaned, flags=re.DOTALL)
    
    # Normalize whitespace and trim
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned
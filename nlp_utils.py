"""
NLP utility functions for hotel booking chatbot.
Uses spaCy for name extraction and dateparser for date parsing.
"""

import re
from datetime import datetime, date
from typing import Optional, Union
import spacy
import dateparser
from rapidfuzz import fuzz


# Load spaCy model - will raise error with helpful message if not installed
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    raise OSError(
        "spaCy English model not found. Please install it by running:\n"
        "python -m spacy download en_core_web_sm"
    )


def extract_name(text: str) -> Optional[str]:
    """
    Extract person names from text using spaCy Named Entity Recognition.

    Args:
        text: Input text that may contain a person's name

    Returns:
        First person name found, or None if no name detected

    Examples:
        extract_name("Hi, I'm John Smith") -> "John Smith"
        extract_name("My name is Alice") -> "Alice"
    """
    if not text or not text.strip():
        return None

    # Process text with spaCy NLP pipeline
    doc = nlp(text.strip())

    # Look for PERSON entities first (most reliable)
    person_entities = [ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"]
    if person_entities:
        return person_entities[0]

    # Fallback: look for capitalized words that could be names
    # Skip common words that shouldn't be names
    skip_words = {'I', 'My', 'Me', 'Hi', 'Hello', 'Hey', 'Sir', 'Madam', 'Mr', 'Mrs', 'Ms'}
    words = text.split()

    for word in words:
        # Check if word is title case and not in skip list
        clean_word = word.strip('.,!?;:"()[]{}')
        if (clean_word.istitle() and
            len(clean_word) > 1 and
            clean_word not in skip_words and
            clean_word.isalpha()):
            return clean_word

    return None


def parse_date(text: str, prefer_future: bool = True) -> Optional[str]:
    """
    Parse natural language dates into ISO format (YYYY-MM-DD).

    Args:
        text: Natural language date string
        prefer_future: If True, ambiguous dates default to future

    Returns:
        ISO date string (YYYY-MM-DD) or None if parsing fails

    Examples:
        parse_date("tomorrow") -> "2024-01-16" (if today is 2024-01-15)
        parse_date("January 15th") -> "2024-01-15"
        parse_date("15/01/2024") -> "2024-01-15"
    """
    if not text or not text.strip():
        return None

    clean_text = text.strip().lower()

    # Configure dateparser settings
    settings = {
        'PREFER_DATES_FROM': 'future' if prefer_future else 'current_period',
        'RETURN_AS_TIMEZONE_AWARE': False,
        'DATE_ORDER': 'DMY'  # Day-Month-Year (change to 'MDY' for US format)
    }

    try:
        # Try dateparser first (handles most natural language)
        parsed_date = dateparser.parse(clean_text, settings=settings)
        if parsed_date:
            return parsed_date.strftime('%Y-%m-%d')

        # Fallback: try common date patterns with regex
        date_patterns = [
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y-%m-%d'),  # ISO format
            (r'(\d{1,2})/(\d{1,2})/(\d{4})', '%d/%m/%Y'),   # DD/MM/YYYY
            (r'(\d{1,2})-(\d{1,2})-(\d{4})', '%d-%m-%Y'),   # DD-MM-YYYY
        ]

        for pattern, date_format in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    parsed_date = datetime.strptime(match.group(), date_format)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue

    except Exception:
        pass

    return None


def is_yes(text: str) -> Optional[bool]:
    """
    Determine if text indicates yes/no response using fuzzy matching.

    Args:
        text: User input text

    Returns:
        True for yes, False for no, None for unclear/neutral

    Examples:
        is_yes("yes please") -> True
        is_yes("nope") -> False
        is_yes("maybe") -> None
    """
    if not text or not text.strip():
        return None

    text_lower = text.strip().lower()

    # Define positive and negative response words
    yes_words = [
        'yes', 'y', 'yeah', 'yep', 'yup', 'sure', 'ok', 'okay', 'alright',
        'definitely', 'absolutely', 'certainly', 'of course', 'please',
        'correct', 'right', 'true', 'confirm', 'agreed'
    ]

    no_words = [
        'no', 'n', 'nope', 'nah', 'not', 'never', 'none', 'negative',
        'false', 'incorrect', 'wrong', 'disagree', 'refuse', 'decline'
    ]

    # Check for exact matches first
    if text_lower in yes_words:
        return True
    if text_lower in no_words:
        return False

    # Use fuzzy matching for partial matches (threshold: 80%)
    for word in yes_words:
        if fuzz.ratio(text_lower, word) >= 80:
            return True

    for word in no_words:
        if fuzz.ratio(text_lower, word) >= 80:
            return False

    # Check if text contains yes/no words
    words = text_lower.split()
    yes_count = sum(1 for word in words if any(fuzz.ratio(word, yes_word) >= 70 for yes_word in yes_words))
    no_count = sum(1 for word in words if any(fuzz.ratio(word, no_word) >= 70 for no_word in no_words))

    if yes_count > no_count:
        return True
    elif no_count > yes_count:
        return False

    return None  # Unclear response


def parse_guests(text: str) -> Optional[int]:
    """
    Extract number of guests from text.

    Args:
        text: Text that may contain guest count

    Returns:
        Number of guests (1-10) or None if not found/invalid

    Examples:
        parse_guests("2 people") -> 2
        parse_guests("five guests") -> 5
        parse_guests("just me") -> 1
    """
    if not text or not text.strip():
        return None

    text_lower = text.strip().lower()

    # Check for single person indicators
    single_indicators = ['me', 'myself', 'just me', 'one person', 'solo', 'alone']
    if any(indicator in text_lower for indicator in single_indicators):
        return 1

    # Look for numeric digits first
    numbers = re.findall(r'\d+', text)
    for num_str in numbers:
        try:
            num = int(num_str)
            if 1 <= num <= 10:  # Reasonable range for hotel guests
                return num
        except ValueError:
            continue

    # Look for written numbers
    word_to_num = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'a': 1, 'an': 1, 'single': 1, 'couple': 2, 'pair': 2
    }

    words = text_lower.split()
    for word in words:
        clean_word = word.strip('.,!?;:"()[]{}')
        if clean_word in word_to_num:
            return word_to_num[clean_word]

    # Use fuzzy matching for number words
    for word in words:
        clean_word = word.strip('.,!?;:"()[]{}')
        for num_word, num_val in word_to_num.items():
            if fuzz.ratio(clean_word, num_word) >= 80:
                return num_val

    return None


def validate_date_order(checkin_str: str, checkout_str: str) -> bool:
    """
    Validate that checkout date is after checkin date.

    Args:
        checkin_str: Check-in date in YYYY-MM-DD format
        checkout_str: Check-out date in YYYY-MM-DD format

    Returns:
        True if checkout > checkin, False otherwise
    """
    try:
        checkin = datetime.strptime(checkin_str, '%Y-%m-%d').date()
        checkout = datetime.strptime(checkout_str, '%Y-%m-%d').date()
        return checkout > checkin
    except ValueError:
        return False
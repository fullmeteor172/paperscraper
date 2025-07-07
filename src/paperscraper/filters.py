# src/paperscraper/filters.py
from __future__ import annotations

import re
from typing import Optional

from .models import AffiliationType

# Keywords that strongly suggest a non-commercial, academic, or research entity.
# Using word boundaries (\b) to avoid matching substrings (e.g., 'corp' in 'incorporate').
ACADEMIC_KEYWORDS = {
    r"\buniversity\b",
    r"\buniversität\b",
    r"\buniversidade\b",
    r"\binstitute\b",
    r"\bhospital\b",
    r"\bschool of medicine\b",
    r"\bmedical center\b",
    r"\bresearch center\b",
    r"\blaboratory\b",
    r"\bcollege\b",
    r"\bacademy\b",
    r"\bfoundation\b",
}

# Keywords that strongly suggest a commercial, for-profit entity.
NON_ACADEMIC_KEYWORDS = {
    r"\bpharmaceuticals\b",
    r"\bbiotech\b",
    r"\btherapeutics\b",
    r"\bdiagnostics\b",
    r"\bventures\b",
    r"\bllc\b",
    r"\binc\b",
    r"\bltd\b",
    r"\bcorp\b",
    r"\bcorporation\b",
    r"\bgmbh\b",
    r"\bag\b",
}

# Compile regex for efficiency
ACADEMIC_RE = re.compile("|".join(ACADEMIC_KEYWORDS), re.IGNORECASE)
NON_ACADEMIC_RE = re.compile("|".join(NON_ACADEMIC_KEYWORDS), re.IGNORECASE)


def classify_affiliation(affiliation: Optional[str]) -> AffiliationType:
    """
    Classify an affiliation string using keyword-based heuristics.

    The function prioritizes non-academic keywords over academic ones in case
    of an overlap.

    Args:
        affiliation: The affiliation text from PubMed.

    Returns:
        The classified affiliation type (NON_ACADEMIC, ACADEMIC, or UNKNOWN).
    """
    if not affiliation:
        return AffiliationType.UNKNOWN

    # Non-academic keywords are often more specific, so check them first.
    if NON_ACADEMIC_RE.search(affiliation):
        return AffiliationType.NON_ACADEMIC

    if ACADEMIC_RE.search(affiliation):
        return AffiliationType.ACADEMIC

    return AffiliationType.UNKNOWN


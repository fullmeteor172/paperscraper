# src/paperscraper/models.py
from __future__ import annotations

"""
Typed domain models used throughout *paperscraper*.

This module contains lightweight, purely-in-memory dataclass representations
for authors and papers as returned by PubMed. Keeping the structures here
separate from any API-specific glue makes them easy to unit-test and reuse.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum, auto
from typing import List, Optional, Sequence

__all__: Sequence[str] = [
    "AffiliationType",
    "Author",
    "Paper",
]


class AffiliationType(Enum):
    """Coarse classification of an author's affiliation."""

    ACADEMIC = auto()
    NON_ACADEMIC = auto()
    UNKNOWN = auto()

    def __str__(self) -> str:
        return self.name.lower()


@dataclass(slots=True)
class Author:
    """Minimal representation of a paper author."""

    name: str
    affiliation: Optional[str] = None
    email: Optional[str] = None
    affiliation_type: AffiliationType = AffiliationType.UNKNOWN

    def is_academic(self) -> bool:
        return self.affiliation_type is AffiliationType.ACADEMIC

    def is_non_academic(self) -> bool:
        return self.affiliation_type is AffiliationType.NON_ACADEMIC

    def is_unknown(self) -> bool:
        return self.affiliation_type is AffiliationType.UNKNOWN


@dataclass(slots=True)
class Paper:
    """Representation of a PubMed article relevant to our scraper."""

    pmid: str
    title: str
    publication_date: date
    authors: List[Author] = field(default_factory=list)
    abstract: Optional[str] = None
    doi: Optional[str] = None
    journal_title: Optional[str] = None
    reference_count: int = 0

    # Derived data helpers
    def academic_authors(self) -> List[Author]:
        """Return authors classified as academic."""
        return [a for a in self.authors if a.is_academic()]

    def non_academic_authors(self) -> List[Author]:
        """Return authors classified as non-academic."""
        return [a for a in self.authors if a.is_non_academic()]

    def unknown_authors(self) -> List[Author]:
        """Return authors with unclassified affiliations."""
        return [a for a in self.authors if a.is_unknown()]

    def company_affiliations(self) -> List[str]:
        """Unique set of company names among non-academic authors."""
        companies = {a.affiliation for a in self.non_academic_authors() if a.affiliation}
        return sorted(list(companies))

    def corresponding_email(self) -> Optional[str]:
        """Return the first email encountered among all authors."""
        for author in self.authors:
            if author.email:
                return author.email
        return None

    def formatted_abstract(self) -> str:
        """Return a clean version of the abstract."""
        if not self.abstract:
            return ""
        return " ".join(self.abstract.split())

    def pubmed_url(self) -> str:
        """Construct a direct URL to the PubMed article."""
        return f"https://pubmed.ncbi.nlm.nih.gov/{self.pmid}/"

    # CSV output helper
    def to_csv_row(self, include_abstract: bool = False) -> List[str]:
        """Return a list of strings suitable for `csv.writer.writerow`."""
        row = [
            self.pmid,
            self.title,
            self.publication_date.isoformat(),
            "; ".join(a.name for a in self.non_academic_authors()),
            "; ".join(a.name for a in self.academic_authors()),
            "; ".join(a.name for a in self.unknown_authors()),
            "; ".join(self.company_affiliations()),
            self.corresponding_email() or "",
            self.doi or "",
            self.journal_title or "",
            str(self.reference_count),
            self.pubmed_url(),
        ]
        if include_abstract:
            row.append(self.formatted_abstract())
        return row
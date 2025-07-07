# src/paperscraper/__init__.py
"""
PaperScraper: A Python tool to fetch and filter PubMed research papers.

This library provides a simple, asynchronous interface to search for articles
on PubMed, classify author affiliations, and filter for papers with authors
from non-academic institutions.

Key Components:
- PubMedClient: The low-level async client for PubMed API interaction.
- Paper, Author, AffiliationType: Data models for representing search results.
- get_papers: A high-level async function for programmatic use.
"""
from __future__ import annotations

import asyncio
from typing import List

from .client import PubMedClient
from .models import AffiliationType, Author, Paper

__all__: list[str] = [
    "get_papers",
    "PubMedClient",
    "Paper",
    "Author",
    "AffiliationType",
]


async def get_papers(
    query: str,
    filter_non_academic: bool = True,
    show_progress: bool = False,
) -> List[Paper]:
    """
    High-level async function to search for papers on PubMed.

    This provides a simple, programmatic entrypoint to the scraper's core
    functionality.

    Args:
        query: The search term for PubMed.
        filter_non_academic: If True, returns only papers with at least one
                             author from a non-academic institution.
                             If False, returns all papers found.
        show_progress: If True, displays a progress bar in the console.

    Returns:
        A list of Paper objects.
    """
    client = PubMedClient(show_progress=show_progress)
    try:
        all_papers = await client.search(query)
        if filter_non_academic:
            return [p for p in all_papers if p.non_academic_authors()]
        return all_papers
    finally:
        await client.aclose()
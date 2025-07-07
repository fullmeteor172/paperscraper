# src/paperscraper/exporter.py
from __future__ import annotations

import csv
from enum import Enum
from pathlib import Path
from typing import Iterable, List, Optional, Set

from rich.console import Console
from rich.table import Table

from .models import Paper

# Define the full set of headers for the output
ALL_HEADERS = [
    "PubmedID",
    "Title", 
    "Publication Date",
    "Non-academic Author(s)",
    "Academic Author(s)",
    "Unknown Author(s)",
    "Company Affiliation(s)",
    "Corresponding Email",
    "DOI",
    "Journal",
    "Reference Count",
    "PubMed URL",
]

DEFAULT_HEADERS = [
    "PubmedID",
    "Title",
    "Publication Date", 
    "Non-academic Author(s)",
    "Company Affiliation(s)",
    "Corresponding Email",
]

MINIMAL_HEADERS = [
    "PubmedID",
    "Title",
    "Company Affiliation(s)",
]


class ColumnSet(str, Enum):
    """Predefined column sets for output."""
    DEFAULT = "default"
    ALL = "all"
    MINIMAL = "minimal"


def _get_headers(
    column_set: ColumnSet, 
    custom_columns: Optional[str], 
    include_abstract: bool
) -> List[str]:
    """Get the list of headers based on column set and options."""
    if custom_columns:
        # Parse custom columns
        headers = [col.strip() for col in custom_columns.split(",")]
        # Validate that all custom columns exist
        valid_headers = set(ALL_HEADERS + (["Abstract"] if include_abstract else []))
        invalid_headers = [h for h in headers if h not in valid_headers]
        if invalid_headers:
            raise ValueError(f"Invalid column names: {invalid_headers}. "
                           f"Valid options: {', '.join(sorted(valid_headers))}")
        return headers
    
    # Use predefined column sets
    if column_set == ColumnSet.DEFAULT:
        headers = DEFAULT_HEADERS[:]
    elif column_set == ColumnSet.ALL:
        headers = ALL_HEADERS[:]
    elif column_set == ColumnSet.MINIMAL:
        headers = MINIMAL_HEADERS[:]
    else:
        headers = DEFAULT_HEADERS[:]
    
    if include_abstract:
        headers.append("Abstract")
    
    return headers


def _get_paper_data(paper: Paper, headers: List[str]) -> List[str]:
    """Get paper data for the specified headers."""
    # Map header names to paper data
    data_map = {
        "PubmedID": paper.pmid,
        "Title": paper.title,
        "Publication Date": paper.publication_date.isoformat(),
        "Non-academic Author(s)": "; ".join(a.name for a in paper.non_academic_authors()),
        "Academic Author(s)": "; ".join(a.name for a in paper.academic_authors()),
        "Unknown Author(s)": "; ".join(a.name for a in paper.unknown_authors()),
        "Company Affiliation(s)": "; ".join(paper.company_affiliations()),
        "Corresponding Email": paper.corresponding_email() or "",
        "DOI": paper.doi or "",
        "Journal": paper.journal_title or "",
        "Reference Count": str(paper.reference_count),
        "PubMed URL": paper.pubmed_url(),
        "Abstract": paper.formatted_abstract(),
    }
    
    return [data_map.get(header, "") for header in headers]


def to_csv(
    papers: Iterable[Paper], 
    file: str, 
    include_abstract: bool = False,
    column_set: ColumnSet = ColumnSet.DEFAULT,
    custom_columns: Optional[str] = None,
) -> None:
    """Write a list of Paper objects to a CSV file."""
    path = Path(file)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    headers = _get_headers(column_set, custom_columns, include_abstract)
    
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        for paper in papers:
            writer.writerow(_get_paper_data(paper, headers))


def to_console(
    papers: Iterable[Paper], 
    include_abstract: bool = False,
    column_set: ColumnSet = ColumnSet.DEFAULT,
    custom_columns: Optional[str] = None,
) -> None:
    """Pretty-print a list of Paper objects to the console using Rich."""
    papers_list = list(papers)  # Convert to list to avoid consuming iterator
    headers = _get_headers(column_set, custom_columns, include_abstract)
    
    table = Table(show_header=True, header_style="bold cyan", box=None, min_width=100)
    
    for header in headers:
        # Adjust column width for readability
        if header in ["Title", "Abstract"]:
            table.add_column(header, overflow="fold", max_width=50)
        elif header in ["Company Affiliation(s)"]:
            table.add_column(header, overflow="fold", max_width=40)
        else:
            table.add_column(header, overflow="fold")
    
    for paper in papers_list:
        table.add_row(*_get_paper_data(paper, headers))
    
    console = Console()
    console.print(table)
    console.print(f"\n[bold green]Found {len(papers_list)} papers with non-academic authors[/bold green]")
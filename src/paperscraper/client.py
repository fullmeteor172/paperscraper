# src/paperscraper/client.py
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import date, datetime
from typing import Iterable, List

import httpx
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

from .filters import classify_affiliation
from .models import Author, Paper

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
FETCH_BATCH_SIZE = 200


class PubMedError(Exception):
    """Custom exception for PubMed API errors."""
    pass


class PubMedClient:
    """Asynchronous client for fetching and parsing data from the PubMed API."""

    def __init__(self, *, show_progress: bool = False, timeout: float = 30.0) -> None:
        self.show_progress = show_progress
        self._client = httpx.AsyncClient(
            timeout=timeout, 
            headers={"User-Agent": "paperscraper/1.0.0"},
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )

    async def search(self, query: str) -> List[Paper]:
        """Return a list of Paper objects matching the PubMed query."""
        if not query.strip():
            raise ValueError("Query cannot be empty")
        
        pmids = await self._esearch(query)
        if not pmids:
            return []

        papers: List[Paper] = []
        progress = Progress(
            SpinnerColumn(),
            BarColumn(),
            TextColumn("[progress.description]{task.description}"),
            TextColumn("[progress.percentage]{task.completed}/{task.total}"),
            TimeElapsedColumn(),
            disable=not self.show_progress,
        )
        
        task = progress.add_task("Fetching paper details...", total=len(pmids))
        
        with progress:
            for i, chunk in enumerate(self._grouper(pmids, FETCH_BATCH_SIZE)):
                try:
                    fetched_papers = await self._efetch(chunk)
                    papers.extend(fetched_papers)
                    progress.update(task, advance=len(chunk))
                except httpx.HTTPStatusError as e:
                    if self.show_progress:
                        progress.console.print(f"[bold red]HTTP Error fetching batch {i+1}: {e}[/bold red]")
                    # Continue with other batches
                    progress.update(task, advance=len(chunk))
                except Exception as e:
                    if self.show_progress:
                        progress.console.print(f"[bold red]Error fetching batch {i+1}: {e}[/bold red]")
                    progress.update(task, advance=len(chunk))
                    
        return papers

    async def aclose(self) -> None:
        """Closes the underlying HTTPX client."""
        await self._client.aclose()

    async def _esearch(self, query: str) -> List[str]:
        """Performs an `esearch` query to get a list of PubMed IDs (PMIDs)."""
        params = {
            "db": "pubmed", 
            "retmax": 10_000, 
            "term": query, 
            "retmode": "json"
        }
        
        try:
            response = await self._client.get(f"{BASE_URL}/esearch.fcgi", params=params)
            response.raise_for_status()
            data = response.json()
            
            # Check for API errors
            if "esearchresult" not in data:
                raise PubMedError(f"Invalid response from PubMed API: {data}")
            
            search_result = data["esearchresult"]
            
            # Check for warnings or errors
            if "warninglist" in search_result:
                warnings = search_result["warninglist"]
                if warnings.get("phrasesnotfound") or warnings.get("quotedphrases"):
                    # This is just a warning, not an error
                    pass
            
            if "errorlist" in search_result:
                errors = search_result["errorlist"]
                if errors.get("phrasesnotfound"):
                    raise PubMedError(f"Invalid search terms: {errors['phrasesnotfound']}")
            
            return search_result.get("idlist", [])
            
        except httpx.RequestError as e:
            raise PubMedError(f"Network error during search: {e}")
        except httpx.HTTPStatusError as e:
            raise PubMedError(f"HTTP error during search: {e}")
        except (KeyError, ValueError) as e:
            raise PubMedError(f"Error parsing search response: {e}")

    async def _efetch(self, pmids: Iterable[str]) -> List[Paper]:
        """Performs an `efetch` query to get detailed article information."""
        params = {
            "db": "pubmed", 
            "rettype": "abstract", 
            "retmode": "xml", 
            "id": ",".join(pmids)
        }
        
        try:
            response = await self._client.get(f"{BASE_URL}/efetch.fcgi", params=params)
            response.raise_for_status()
            return list(self._parse_xml(response.text))
        except httpx.RequestError as e:
            raise PubMedError(f"Network error during fetch: {e}")
        except httpx.HTTPStatusError as e:
            raise PubMedError(f"HTTP error during fetch: {e}")

    def _parse_xml(self, xml_text: str) -> Iterable[Paper]:
        """Parses the XML from an efetch response into Paper objects."""
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            raise PubMedError(f"Error parsing XML response: {e}")
        
        for article in root.findall(".//PubmedArticle"):
            try:
                paper = self._parse_article(article)
                if paper:
                    yield paper
            except Exception as e:
                # Skip malformed articles but continue processing others
                pmid = article.findtext(".//PMID", "unknown")
                if self.show_progress:
                    print(f"Warning: Skipping article {pmid} due to parsing error: {e}")
                continue

    def _parse_article(self, article: ET.Element) -> Paper | None:
        """Parse a single PubmedArticle element into a Paper object."""
        pmid = article.findtext(".//PMID")
        if not pmid:
            return None

        # Core fields
        title = article.findtext(".//ArticleTitle") or "(no title)"
        abstract_nodes = article.findall(".//Abstract/AbstractText")
        abstract = "\n".join(node.text for node in abstract_nodes if node.text)
        pub_date = self._parse_date(article)
        doi = article.findtext(".//ArticleId[@IdType='doi']")
        journal_title = article.findtext(".//Journal/Title")
        ref_count = len(article.findall(".//ReferenceList/Reference"))

        # Author parsing
        authors: List[Author] = []
        for author_el in article.findall(".//Author"):
            name_parts = [
                author_el.findtext("ForeName") or "", 
                author_el.findtext("LastName") or ""
            ]
            full_name = " ".join(p for p in name_parts if p).strip() or "(anonymous)"
            affil_node = author_el.find(".//AffiliationInfo/Affiliation")
            affil_text = affil_node.text if affil_node is not None else None
            email = self._extract_email(affil_text)
            affil_type = classify_affiliation(affil_text)
            authors.append(Author(full_name, affil_text, email, affil_type))

        return Paper(
            pmid=pmid,
            title=title,
            publication_date=pub_date,
            authors=authors,
            abstract=abstract or None,
            doi=doi,
            journal_title=journal_title,
            reference_count=ref_count,
        )

    @staticmethod
    def _grouper(seq: List[str], size: int) -> Iterable[List[str]]:
        """Yields successive n-sized chunks from a list."""
        for i in range(0, len(seq), size):
            yield seq[i : i + size]

    @staticmethod
    def _extract_email(affil: str | None) -> str | None:
        """Extracts an email address from affiliation text."""
        if not affil:
            return None
        match = EMAIL_RE.search(affil)
        return match.group(0) if match else None

    def _parse_date(self, article_el: ET.Element) -> date:
        """Parses the publication date from various XML formats."""
        year_str = article_el.findtext(".//PubDate/Year")
        if year_str:
            month_str = article_el.findtext(".//PubDate/Month") or "1"
            day_str = article_el.findtext(".//PubDate/Day") or "1"
            try:
                return datetime(
                    int(year_str), 
                    self._month_to_int(month_str), 
                    int(day_str)
                ).date()
            except (ValueError, TypeError):
                return datetime(int(year_str), 1, 1).date()

        medline_date = article_el.findtext(".//MedlineDate")
        if medline_date:
            try:
                year_match = re.search(r"\b(\d{4})\b", medline_date)
                if year_match:
                    return datetime(int(year_match.group(1)), 1, 1).date()
            except ValueError:
                pass
        
        return date.today()

    @staticmethod
    def _month_to_int(m: str) -> int:
        """Converts month string (e.g., 'Jan', '01') to an integer."""
        _MONTHS = {
            "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
            "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
        }
        if m.isdigit():
            return max(1, min(12, int(m)))  # Clamp to valid month range
        return _MONTHS.get(m[:3].title(), 1)
# src/paperscraper/__main__.py
from __future__ import annotations

import asyncio
from typing import Optional

import typer
from rich import print
from rich.console import Console

from .client import PubMedClient
from .exporter import to_console, to_csv, ColumnSet

app = typer.Typer(
    add_completion=False,
    help="A CLI tool to fetch and filter research papers from PubMed.",
    rich_markup_mode="markdown",
)

console = Console()

@app.command()
def main(
    query: str = typer.Argument(help="PubMed query string (use quotes for multiple words)."),
    file: Optional[str] = typer.Option(
        None, "--file", "-f", help="Save results to a CSV file (e.g., 'results.csv')."
    ),
    columns: str = typer.Option(
        "default", "--columns", "-c", 
        help="Column set to include: 'default', 'all', or 'minimal'."
    ),
    custom_columns: Optional[str] = typer.Option(
        None, "--custom-columns", 
        help="Comma-separated list of custom columns (overrides --columns)."
    ),
    include_abstract: bool = typer.Option(
        False, "--include-abstract", "-a", help="Include the paper's abstract in the output."
    ),
    show_progress: bool = typer.Option(
        True, "--progress/--no-progress", help="Display a progress bar during fetching."
    ),
    debug: bool = typer.Option(
        False, "--debug", "-d", help="Print debug information during execution."
    ),
) -> None:
    """
    Fetch papers that have at least one author from a non-academic institution.
    
    **Examples:**
    
    ```bash
    # Basic search with default columns
    get-papers-list "cancer AND drug discovery"
    
    # Save to CSV with all columns
    get-papers-list "CRISPR" -f results.csv --columns all
    
    # Custom columns only
    get-papers-list "immunotherapy" --custom-columns "PubmedID,Title,Company Affiliation(s)"
    
    # Include abstracts
    get-papers-list "machine learning" --include-abstract
    ```
    """
    # Validate columns parameter
    if columns not in ["default", "all", "minimal"]:
        console.print(f"[bold red]Error: Invalid column set '{columns}'. Must be 'default', 'all', or 'minimal'.[/bold red]")
        raise typer.Exit(1)
    
    column_set = ColumnSet(columns)
    
    if debug:
        console.print(f"[dim]Debug mode enabled[/dim]")
        console.print(f"[dim]Query: {query}[/dim]")
        console.print(f"[dim]Columns: {column_set}[/dim]")
        console.print(f"[dim]Custom columns: {custom_columns}[/dim]")
        console.print(f"[dim]Include abstract: {include_abstract}[/dim]")
    
    print(f"[bold green]Searching PubMed for:[/bold green] [yellow]'{query}'[/yellow]")

    async def _run() -> None:
        client = PubMedClient(show_progress=show_progress)
        try:
            # 1. Fetch all papers matching the query
            if debug:
                console.print("[dim]Fetching papers from PubMed...[/dim]")
            
            all_papers = await client.search(query)
            
            if debug:
                console.print(f"[dim]Found {len(all_papers)} total papers[/dim]")

            # 2. Filter for papers with at least one non-academic author
            filtered_papers = [p for p in all_papers if p.non_academic_authors()]
            
            if debug:
                console.print(f"[dim]Filtered to {len(filtered_papers)} papers with non-academic authors[/dim]")

            if not filtered_papers:
                print("[bold yellow]No papers found with non-academic authors for this query.[/bold yellow]")
                print("[dim]Try broadening your search terms or checking for typos.[/dim]")
                return

            # 3. Output the results
            if file:
                to_csv(filtered_papers, file, include_abstract, column_set, custom_columns)
                print(f"[green]✓ Saved {len(filtered_papers)} papers to [bold]{file}[/bold][/green]")
            else:
                to_console(filtered_papers, include_abstract, column_set, custom_columns)

        except Exception as e:
            if debug:
                console.print(f"[bold red]Error: {e}[/bold red]")
                raise
            else:
                console.print(f"[bold red]Error: {e}[/bold red]")
                console.print("[dim]Use --debug flag for more details[/dim]")
        finally:
            await client.aclose()

    asyncio.run(_run())


if __name__ == "__main__":
    app()
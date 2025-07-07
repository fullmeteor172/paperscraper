# [PubMed-Paper Scraper](https://test.pypi.org/project/pubmed-paperscraper/0.1.0/)

A Python CLI tool and library for fetching **research papers with non-academic authors** from PubMed. This tool identifies papers where at least one author is affiliated with pharmaceutical companies, biotech firms, or other commercial organizations.

## Features

- 🔍 **Flexible Search**: Support for PubMed's full query syntax
- 🏢 **Smart Filtering**: Automatically identifies non-academic authors using keyword heuristics
- 📊 **Multiple Output Formats**: Console display or CSV export
- 🎛️ **Customizable Columns**: Choose from predefined sets or create custom column layouts
- 📈 **Progress Tracking**: Visual progress bars for long-running searches
- 🔧 **Programmatic API**: Use as a Python module in your own projects
- ⚡ **Async Performance**: Fast, concurrent API calls with connection pooling

## Installation

### Prerequisites

- Python 3.10 or higher
- Poetry (for dependency management)

### Install Dependencies

```bash
git clone https://github.com/yourusername/paperscraper.git
cd paperscraper
poetry install
```

### Activate the Virtual Environment

```bash
poetry shell
```

## Command Line Usage

### Basic Usage

```bash
# Search for papers and display results in console
get-papers-list "cancer AND drug discovery"

# Save results to CSV file
get-papers-list "CRISPR" -f results.csv

# Include abstracts in output
get-papers-list "immunotherapy" --include-abstract -f results.csv
```

### Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--file` | `-f` | Save results to CSV file | Console output |
| `--columns` | `-c` | Column set: `default`, `all`, or `minimal` | `default` |
| `--custom-columns` |  | Comma-separated list of custom columns | None |
| `--include-abstract` | `-a` | Include paper abstracts in output | False |
| `--progress` |  | Show/hide progress bar | True |
| `--no-progress` |  | Disable progress bar | False |
| `--debug` | `-d` | Print debug information | False |
| `--help` | `-h` | Show help message | |

### Available Columns

#### All Available Columns
- `PubmedID`: Unique PubMed identifier
- `Title`: Paper title
- `Publication Date`: Publication date (YYYY-MM-DD format)
- `Non-academic Author(s)`: Authors from commercial organizations
- `Academic Author(s)`: Authors from academic institutions
- `Unknown Author(s)`: Authors with unclassified affiliations
- `Company Affiliation(s)`: Names of commercial organizations
- `Corresponding Email`: Email of corresponding author
- `DOI`: Digital Object Identifier
- `Journal`: Journal name
- `Reference Count`: Number of references cited
- `PubMed URL`: Direct link to PubMed article
- `Abstract`: Paper abstract (when `--include-abstract` is used)

#### Predefined Column Sets

**Default Columns:**
- PubmedID, Title, Publication Date, Non-academic Author(s), Company Affiliation(s), Corresponding Email

**Minimal Columns:**
- PubmedID, Title, Company Affiliation(s)

**All Columns:**
- All available columns listed above

### Query Examples

```bash
# Basic search
get-papers-list "machine learning"

# Complex PubMed query
get-papers-list "((cancer[MeSH]) AND (drug therapy[MeSH])) AND (2020[PDAT]:2024[PDAT])"

# Search with author names
get-papers-list "Smith J[Author] AND diabetes"

# Journal-specific search
get-papers-list "Nature[Journal] AND CRISPR"

# Search by date range
get-papers-list "COVID-19 AND 2020[PDAT]:2024[PDAT]"
```

### Output Format Examples

```bash
# Use minimal columns
get-papers-list "gene therapy" --columns minimal

# Use all available columns
get-papers-list "biomarkers" --columns all -f comprehensive_results.csv

# Custom column selection
get-papers-list "drug discovery" --custom-columns "PubmedID,Title,DOI,Journal"

# Include abstracts with default columns
get-papers-list "personalized medicine" --include-abstract -f results_with_abstracts.csv
```

## Programmatic Usage

### Basic Module Usage

```python
import asyncio
from paperscraper import get_papers

async def main():
    # Search for papers with non-academic authors
    papers = await get_papers(
        query="cancer AND drug discovery",
        filter_non_academic=True,
        show_progress=True
    )
    
    print(f"Found {len(papers)} papers")
    
    for paper in papers[:5]:  # Show first 5 results
        print(f"- {paper.title}")
        print(f"  PMID: {paper.pmid}")
        print(f"  Companies: {', '.join(paper.company_affiliations())}")
        print()

# Run the async function
asyncio.run(main())
```

### Advanced Module Usage

```python
import asyncio
from paperscraper import PubMedClient, Paper
from paperscraper.exporter import to_csv, ColumnSet

async def advanced_search():
    # Create client with custom settings
    client = PubMedClient(show_progress=True, timeout=60.0)
    
    try:
        # Search for all papers (not just non-academic)
        all_papers = await client.search("machine learning AND healthcare")
        
        # Filter manually
        industry_papers = [p for p in all_papers if p.non_academic_authors()]
        academic_papers = [p for p in all_papers if p.academic_authors()]
        
        print(f"Total papers: {len(all_papers)}")
        print(f"Industry papers: {len(industry_papers)}")
        print(f"Academic papers: {len(academic_papers)}")
        
        # Export to CSV with custom settings
        to_csv(
            industry_papers,
            "industry_papers.csv",
            include_abstract=True,
            column_set=ColumnSet.ALL
        )
        
        # Access individual paper data
        for paper in industry_papers[:3]:
            print(f"\nPaper: {paper.title}")
            print(f"Journal: {paper.journal_title}")
            print(f"Date: {paper.publication_date}")
            print(f"DOI: {paper.doi}")
            print(f"URL: {paper.pubmed_url()}")
            
            # Author information
            for author in paper.non_academic_authors():
                print(f"  Non-academic author: {author.name}")
                print(f"    Affiliation: {author.affiliation}")
                print(f"    Email: {author.email}")
    
    finally:
        await client.aclose()

asyncio.run(advanced_search())
```

### Working with Paper Objects

```python
from paperscraper.models import Paper, Author, AffiliationType

# Papers have rich metadata
paper = papers[0]  # Assuming you have papers from a search

# Basic information
print(f"Title: {paper.title}")
print(f"PMID: {paper.pmid}")
print(f"Publication Date: {paper.publication_date}")
print(f"Journal: {paper.journal_title}")
print(f"DOI: {paper.doi}")
print(f"Reference Count: {paper.reference_count}")

# Author analysis
academic_authors = paper.academic_authors()
non_academic_authors = paper.non_academic_authors()
unknown_authors = paper.unknown_authors()

print(f"Academic authors: {len(academic_authors)}")
print(f"Non-academic authors: {len(non_academic_authors)}")
print(f"Unknown affiliation authors: {len(unknown_authors)}")

# Company information
companies = paper.company_affiliations()
print(f"Companies involved: {', '.join(companies)}")

# Contact information
email = paper.corresponding_email()
print(f"Corresponding email: {email}")

# Abstract
abstract = paper.formatted_abstract()
print(f"Abstract: {abstract[:200]}...")  # First 200 characters
```

## How It Works

### Author Classification

The tool uses keyword-based heuristics to classify author affiliations:

**Non-Academic Keywords:**
- `pharmaceuticals`, `biotech`, `therapeutics`, `diagnostics`
- `ventures`, `llc`, `inc`, `ltd`, `corp`, `corporation`
- `gmbh`, `ag`

**Academic Keywords:**
- `university`, `institut`, `hospital`, `school of medicine`
- `medical center`, `research center`, `laboratory`
- `college`, `academy`, `foundation`

### Search Process

1. **Query Execution**: Sends search query to PubMed API using `esearch`
2. **Paper Fetching**: Retrieves detailed paper information using `efetch`
3. **Author Classification**: Analyzes author affiliations using keyword matching
4. **Filtering**: Returns only papers with at least one non-academic author
5. **Output**: Formats results for console display or CSV export

## Error Handling

The tool includes robust error handling for:
- Invalid PubMed queries
- Network timeouts and connectivity issues
- Malformed XML responses
- Missing or incomplete paper data
- File system errors during CSV export

## Development Tools Used

This project was built with assistance from:
- **Claude AI**: Code Refactoring, Documentation
- **GitHub Co-Pilot**: AI code completion
- **Chat GPT**: Debug Aid
- **Poetry**: Dependency management and packaging
- **Rich**: Beautiful console output and progress bars
- **httpx**: Modern async HTTP client
- **Typer**: Type-safe CLI framework

## Dependencies

### Core Dependencies
- `httpx>=0.27.0`: Async HTTP client for PubMed API
- `typer>=0.12.3`: CLI framework
- `rich>=13.7.1`: Console formatting and progress bars
- `pandas>=2.2.2`: Data manipulation
- `lxml>=6.0.0`: XML parsing

### Development Dependencies
- `mypy>=1.10`: Type checking
- `pytest>=8.2`: Testing framework
- `pytest-asyncio>=0.23`: Async testing support
- `ruff>=0.4`: Code formatting and linting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `poetry run pytest`
5. Check types: `poetry run mypy src/`
6. Format code: `poetry run ruff format src/`
7. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the PubMed API documentation for query syntax
- Review the examples in this README for common use cases
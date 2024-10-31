import re
import requests
from datetime import datetime, timezone
from xml.etree import ElementTree as ET

from database import Paper

# Crossref API URL
CROSSREF_API_URL = "https://api.crossref.org/works/"

ATOM = "{http://www.w3.org/2005/Atom}"

def sanitize_doi(doi: str) -> dict:
    """
    Sanitize and classify the input to determine if it's a standard DOI, arXiv ID, or arXiv DOI.
    Returns a dictionary with type ('doi' or 'arxiv') and the identifier.
    """
    # Patterns for recognizing arXiv identifiers and standard DOIs
    # I love llms for that regex magic
    arxiv_pattern = re.compile(r'(arxiv:|https?://arxiv.org/abs/)?(\d{4}\.\d{4,5}(v\d+)?|[a-z\-]+/\d{7})')
    doi_pattern = re.compile(r'(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)')

    arxiv_match = arxiv_pattern.search(doi)
    doi_match = doi_pattern.search(doi)

    if arxiv_match:
        return {"type": "arxiv", "identifier": arxiv_match.group(2)}
    elif doi_match:
        return {"type": "doi", "identifier": doi_match.group(1)}
    else:
        raise ValueError("Invalid DOI or arXiv identifier")

def fetch_crossref_details(doi: str) -> dict:
    """Fetch paper details using the Crossref API for a standard DOI."""
    url = f"{CROSSREF_API_URL}{doi}"
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError("Could not retrieve details from Crossref")

    data = response.json().get("message", {})
    return {
        "doi": f"{doi}",
        "title": data.get("title", ["No title available"])[0],
        "authors": ", ".join([f"{author['given']} {author['family']}" for author in data.get("author", [])]), # Use CSV field, not so elegant
        "abstract": data.get("abstract", "No abstract available"),
        "journal": data["container-title"][0],
        "volume": data.get("volume", 0),
        "published": datetime(*data["published"]["date-parts"][0])
    }

def fetch_arxiv_details(arxiv_id: str) -> dict:
    """Fetch paper details using the arXiv API for an arXiv identifier. 
    Crossref does not process arXiv DOIs. """
    url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError("Could not retrieve details from arXiv")

    root = ET.fromstring(response.content)
    entry = root.find(f"{ATOM}entry")

    title = entry.find(f"{ATOM}title").text.strip()
    authors = [author.find(f"{ATOM}name").text for author in entry.findall(f"{ATOM}author")]
    abstract = entry.find(f"{ATOM}summary").text
    published = entry.find(f"{ATOM}published").text.strip()

    return {
        "doi": f"10.48550/{arxiv_id}",
        "title": title.strip(),
        "authors": ", ".join(authors),
        "abstract": abstract.strip(),
        "journal": "arXiv",
        "volume": arxiv_id,
        "published": datetime.strptime(published, '%Y-%m-%dT%H:%M:%SZ')

    }

def fetch_paper_details(identifier: str) -> dict:
    """
    Fetch paper details based on the identifier. Uses Crossref API for DOIs and arXiv API for arXiv IDs.
    """
    sanitized = sanitize_doi(identifier)

    if sanitized["type"] == "doi":
        return fetch_crossref_details(sanitized["identifier"])
    elif sanitized["type"] == "arxiv":
        return fetch_arxiv_details(sanitized["identifier"])
    else:
        raise ValueError("Unsupported identifier type")

def create_paper(paper_details: dict, added_by: str) -> Paper:
    return Paper(
            doi=paper_details["doi"],
            title=paper_details["title"],
            authors=paper_details["authors"],
            abstract=paper_details["abstract"],
            journal=paper_details["journal"],
            volume=paper_details["volume"],
            published=paper_details["published"],
            added_by=added_by,
            created_at=datetime.now(timezone.utc))

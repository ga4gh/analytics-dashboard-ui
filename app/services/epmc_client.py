"""
EPMC (Europe PubMed Central) API client.
Mirrors the pattern used by pypi_client.py and github_client.py.
"""

import requests
import pandas as pd
import json
import app.constants.api as api_constants


def get_json(endpoint):
    """
    Generic GET → JSON helper (same as pypi_client.get_json).
    """
    print(f"Calling API: {endpoint}")
    resp = requests.get(endpoint, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_all_paginated(endpoint, limit=1000):
    """
    Fetch all pages from an endpoint that supports `limit` and `skip` query params.
    Returns a list of items when the endpoint is paginated, or the original
    response if it is non-list/dict.
    """
    items = []
    skip = 0

    while True:
        params = {"limit": limit, "skip": skip}
        resp = requests.get(endpoint, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # If the endpoint returns a dict with 'results' list
        if isinstance(data, dict):
            if "results" in data and isinstance(data["results"], list):
                page = data["results"]
            elif isinstance(data.get("items"), list):
                page = data.get("items")
            else:
                # Not a paginated list; return the dict directly
                return data

        elif isinstance(data, list):
            page = data

        else:
            return data

        if not page:
            break

        items.extend(page)

        if len(page) < limit:
            break

        skip += limit

    return items


# ---------------------------------------------------------------------------
# Data-fetching helpers – one per EPMC endpoint
# ---------------------------------------------------------------------------

def get_all_latest_entries():
    """
    Fetch the latest EPMC entries from the backend.
    Returns:
        list[dict]: raw JSON list of entry records.
    """
    data = get_all_paginated(api_constants.EPMC_ALL_LATEST_ENTRIES)
    # If the paginated getter returned a dict (non-paginated response), try to
    # extract a list from common keys, otherwise wrap single dict in list.
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("results") or data.get("items") or [data]
    return []


def get_affiliation_countries_count():
    """
    Fetch country-level affiliation counts.
    Returns:
        list[dict]: e.g. [{"country": "US", "count": 42}, ...]
    """
    # Countries endpoint returns a mapping of country -> count (single request)
    data = get_json(api_constants.EPMC_AFFILIATION_COUNTRIES_COUNT)
    # Expect exactly a dict like {"United States": 5278, ...}
    if isinstance(data, dict):
        return data
    # If for some reason a list is returned, pass it through (but callers expect dict)
    if isinstance(data, list):
        return data
    return {}


def get_all_pmc_authors():
    """
    Fetch all PMC authors.
    Returns:
        list[dict]: author records.
    """
    # Authors endpoint returns a list of author records (paginated)
    data = get_all_paginated(api_constants.EPMC_ALL_PMC_AUTHORS)
    # Expect a list of dicts like [{'fullname':..., 'id':...}, ...]
    return data if isinstance(data, list) else []


def get_unique_citations():
    """
    Fetch the total unique citations value from the backend.
    Returns an integer when possible, otherwise 0.
    """
    # Citations endpoint returns a list of citation records; count unique citations
    data = get_json(api_constants.EPMC_UNIQUE_CITATIONS)
    return data.get("citation_count", 0) if isinstance(data, dict) else 0

def get_unique_authors_count():
    """
    Fetch the total unique authors count from the backend.
    Returns an integer when possible, otherwise 0.
    """
    # Unique authors endpoint returns a dict with 'unique_authors_count' key
    data = get_json(api_constants.EPMC_UNIQUE_AUTHOR_COUNT)
    return data.get("unique_authors", 0) if isinstance(data, dict) else 0


def get_top_authors(count=30):
    """
    Fetch top authors by publication count from the backend.
    Returns:
        list[dict]: pre-computed top authors sorted by count, each with 'author', 'author_count', 'author_id'.
    """
    endpoint = api_constants.EPMC_TOP_AUTHORS
    params = {"count": count}
    print(f"Calling API: {endpoint} with count={count}")
    resp = requests.get(endpoint, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data if isinstance(data, list) else []


def get_all_articles():
    """
    Fetch all articles summary from the backend.
    Returns the raw JSON (expected dict with keys 'article_count' and 'articles').
    """
    data = get_json(api_constants.EPMC_ALL_ARTICLES)
    return data if isinstance(data, dict) else {}


def get_epmc_article_count():
    """
    Convenience helper to return the integer article_count from the
    `epmc/all-articles` endpoint.
    """
    data = get_all_articles()
    return int(data.get("article_count", 0)) if isinstance(data, dict) else 0


# ---------------------------------------------------------------------------
# Convenience: prepare a DataFrame ready for the layout / callbacks
# ---------------------------------------------------------------------------

def prepare_epmc_data():
    """
    Fetch and lightly process all EPMC data needed by the dashboard page.

    Returns:
        tuple: (entries_df, countries_df, authors_df, total_entries)
    """
    # Prefer the consolidated all-articles endpoint when available (contains
    # article_count and articles list). Fall back to the paginated latest-entries
    # endpoint for older deployments.
    all_articles_resp = get_all_articles()
    if isinstance(all_articles_resp, dict) and "articles" in all_articles_resp:
        raw_entries = all_articles_resp.get("articles", [])
        total_entries = int(all_articles_resp.get("article_count", len(raw_entries)))
    else:
        raw_entries = get_all_latest_entries()
    raw_countries = get_affiliation_countries_count()
    raw_authors = get_all_pmc_authors()

    # Entries: only use the consolidated `all-articles` response when available.
    # Build a sanitized list of flat records that the DataTable can render.
    entries_df = pd.DataFrame()
    if isinstance(all_articles_resp, dict) and isinstance(raw_entries, list):
        sanitized = []
        for e in raw_entries:
            # Extract only simple scalar fields. If missing, use empty string or None.
            record = {
                "title": e.get("title") or "",
                "doi": e.get("doi") or "",
                "pub_year": e.get("pub_year") or e.get("year") or "",
                # keep a serialized copy of the full article record for details view
                "raw_json": json.dumps(e, ensure_ascii=False),
            }
            sanitized.append(record)
        entries_df = pd.DataFrame.from_records(sanitized)

    # Countries: expect a dict mapping country -> count
    if isinstance(raw_countries, dict):
        items = [{"country": k, "count": v} for k, v in raw_countries.items()]
        countries_df = pd.DataFrame.from_records(items)
    else:
        countries_df = pd.DataFrame()

    # Authors: expect a list of dicts with 'fullname' etc.
    authors_df = pd.DataFrame.from_records(raw_authors) if raw_authors and isinstance(raw_authors, list) else pd.DataFrame()

    # If total_entries wasn't derived from all-articles response above, compute
    # from the entries dataframe length.
    if 'total_entries' not in locals():
        total_entries = len(entries_df)

    return entries_df, countries_df, authors_df, total_entries

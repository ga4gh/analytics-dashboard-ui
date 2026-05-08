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
        print(f"Calling API: {endpoint} params={params}")
        resp = requests.get(endpoint, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # If the endpoint returns a dict with a paginated list payload
        if isinstance(data, dict):
            if "results" in data and isinstance(data["results"], list):
                page = data["results"]
            elif isinstance(data.get("items"), list):
                page = data.get("items")
            elif isinstance(data.get("articles"), list):
                page = data.get("articles")
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

def get_all_articles(limit=1000):
    """Fetch all EPMC articles using limit/skip pagination."""
    data = get_all_paginated(api_constants.EPMC_ALL_ARTICLES, limit=limit)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("articles") or data.get("results") or data.get("items") or [data]
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

# Compute countries stats limited to whitelist
def _countries_stats_whitelist(df, whitelist):
    if df is None or df.empty:
        return 0, 0
    cols = list(df.columns)
    if "country" in [c.lower() for c in cols] and "count" in [c.lower() for c in cols]:
        country_col = next(c for c in cols if c.lower() == "country")
        count_col = next(c for c in cols if c.lower() == "count")
        tmp = df[[country_col, count_col]].copy()
        tmp.columns = ["country", "count"]
    else:
        tmp = df.iloc[:, :2].copy()
        tmp.columns = ["country", "count"]
    tmp["country_norm"] = tmp["country"].astype(str).str.strip()
    whitelist_set = {c.strip().lower() for c in whitelist}
    tmp = tmp[tmp["country_norm"].str.lower().isin(whitelist_set)]
    num_countries = int(tmp["country_norm"].nunique())
    total_counts = int(pd.to_numeric(tmp["count"], errors="coerce").fillna(0).sum())
    return num_countries, total_counts
    
# Total citations: robust count from cached payload (list or dict containing list)
def _count_citations_payload(cit):
    if cit is None:
        return 0
    if isinstance(cit, list):
        return len(cit)
    if isinstance(cit, dict):
        for k in ("results", "items", "citations", "data"):
            if k in cit and isinstance(cit[k], list):
                return len(cit[k])
        # fallback: if dict directly contains a numeric summary
        if "citation_count" in cit and isinstance(cit["citation_count"], (int, float)):
            return int(cit["citation_count"])
        return 0
    return 0

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


def get_authors_by_article(pm_id):
    """
    Fetch authors for a specific article by PM id using the configured API endpoint.
    Returns a list of author dicts (may be empty).
    """
    if not pm_id:
        return []
    try:
        endpoint = api_constants.EPMC_GET_AUTHORS_BY_ARTICLE + str(pm_id)
        data = get_json(endpoint)
        if isinstance(data, list):
            return data
        # If API returns a dict with 'results' or 'items'
        if isinstance(data, dict):
            if "results" in data and isinstance(data["results"], list):
                return data["results"]
            if "items" in data and isinstance(data["items"], list):
                return data["items"]
        return []
    except Exception:
        return []





# ---------------------------------------------------------------------------
# Convenience: prepare a DataFrame ready for the layout / callbacks
# ---------------------------------------------------------------------------

_epmc_cache = {}

def prepare_epmc_data():
    """
    Fetch and process all EPMC data in a single pass to avoid redundant API calls.
    Returns all data needed for the dashboard: DataFrames, counts, and metadata.
    Results are cached after the first call.

    Returns:
        tuple: (entries_df, countries_df, authors_df, total_entries, citations,
                unique_authors_count, top_authors_data)
    """

    # Fetch all API data upfront (no redundancy)
    raw_entries = get_all_articles(limit=1000)
    total_entries = len(raw_entries)
    
    raw_countries = get_affiliation_countries_count()
    raw_authors = get_all_pmc_authors()
    
    unique_authors_resp = get_json(api_constants.EPMC_UNIQUE_AUTHOR_COUNT)
    unique_authors_count = unique_authors_resp.get("unique_authors", 0) if isinstance(unique_authors_resp, dict) else 0
    
    top_authors_resp = get_json(api_constants.EPMC_TOP_AUTHORS)
    top_authors_data = top_authors_resp if isinstance(top_authors_resp, list) else []
    
    citations = get_json(api_constants.EPMC_CITATION_OVER_YEARS)

    # Build entries DataFrame
    entries_df = pd.DataFrame()
    if isinstance(raw_entries, list):
        sanitized = []
        for e in raw_entries:
            record = {
                "title": e.get("title") or "",
                "doi": e.get("doi") or "",
                "pub_year": e.get("pub_year") or e.get("year") or "",
                "raw_json": json.dumps(e, ensure_ascii=False),
            }
            sanitized.append(record)
        entries_df = pd.DataFrame.from_records(sanitized) if sanitized else pd.DataFrame()

    # Build countries DataFrame
    if isinstance(raw_countries, dict):
        items = [{"country": k, "count": v} for k, v in raw_countries.items()]
        countries_df = pd.DataFrame.from_records(items)
    else:
        countries_df = pd.DataFrame()

    # Build authors DataFrame
    authors_df = pd.DataFrame.from_records(raw_authors) if raw_authors and isinstance(raw_authors, list) else pd.DataFrame()

    result = (entries_df, countries_df, authors_df, total_entries, citations, unique_authors_count, top_authors_data)
    _epmc_cache["result"] = result
    return result

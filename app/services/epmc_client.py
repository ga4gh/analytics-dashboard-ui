import datetime
import logging
import requests
import pandas as pd
import app.constants.api as api_constants

logger = logging.getLogger(__name__)


def get_json(endpoint):
    """
    Generic GET → JSON helper (same as pypi_client.get_json).
    """
    logger.debug("Calling API: %s", endpoint)
    resp = requests.get(endpoint, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_all_paginated(endpoint, limit=1000, timeout=120):
    """
    Fetch all pages from an endpoint that supports `limit` and `skip` query params.
    Returns a list of items when the endpoint is paginated, or the original
    response if it is non-list/dict.
    """
    items = []
    skip = 0

    while True:
        params = {"limit": limit, "skip": skip}
        logger.debug("Calling API: %s params=%s", endpoint, params)
        resp = requests.get(endpoint, params=params, timeout=timeout)
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


def get_affiliations_by_article(pm_id):
    """
    Fetch affiliation rows for a specific article by PM id using the configured API endpoint.
    Returns a list of affiliation/author rows (may be empty).
    """
    if not pm_id:
        return []
    try:
        endpoint = api_constants.EPMC_AFFILIATION_BY_ARTICLE + str(pm_id)
        data = get_json(endpoint)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            if "results" in data and isinstance(data["results"], list):
                return data["results"]
            if "items" in data and isinstance(data["items"], list):
                return data["items"]
        return []
    except Exception:
        return []





def _normalize_pub_year(value):
    """Return a 4-digit publication year as int, or None when invalid."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    try:
        year = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return year if 1000 <= year <= 9999 else None

def prepare_epmc_data():
    """
    Fetch and process all EPMC data in a single pass to avoid redundant API calls.
    Returns all data needed for the dashboard: DataFrames, counts, and metadata.

    Returns:
        tuple: (entries_df, countries_df, authors_df, total_entries, citations,
                unique_authors_count, top_authors_data)
    """
    # Use the lightweight endpoint — returns only the 5 scalar columns the dashboard
    # needs (title, doi, pub_year, cited_by_count, is_open_access) via a fast
    # DISTINCT ON query. Avoids loading abstract_text, affiliations, and all
    # relationships that the heavy /epmc/all-articles endpoint loaded.
    try:
        resp = requests.get(api_constants.EPMC_ARTICLES_LIGHT, timeout=120)
        resp.raise_for_status()
        light_data = resp.json()
        raw_entries = light_data.get("articles", []) if isinstance(light_data, dict) else []
        total_entries = light_data.get("article_count", len(raw_entries)) if isinstance(light_data, dict) else len(raw_entries)
    except Exception as exc:
        logger.warning("Failed to fetch articles-light: %s", exc)
        raw_entries = []
        total_entries = 0

    raw_countries = get_affiliation_countries_count()

    unique_authors_resp = get_json(api_constants.EPMC_UNIQUE_AUTHOR_COUNT)
    unique_authors_count = unique_authors_resp.get("unique_authors", 0) if isinstance(unique_authors_resp, dict) else 0

    top_authors_resp = get_json(api_constants.EPMC_TOP_AUTHORS)
    top_authors_data = top_authors_resp if isinstance(top_authors_resp, list) else []

    citations = get_json(api_constants.EPMC_CITATION_OVER_YEARS)

    # Build entries DataFrame
    entries_df = pd.DataFrame()
    if isinstance(raw_entries, list) and raw_entries:
        sanitized = []
        for e in raw_entries:
            pub_year = _normalize_pub_year(e.get("pub_year") or e.get("year"))
            sanitized.append({
                "pm_id":          e.get("pm_id") or "",
                "title":          e.get("title") or "",
                "doi":            e.get("doi") or "",
                "pub_year":       pub_year,
                "cited_by_count": int(e.get("cited_by_count") or 0),
                "is_open_access": bool(e.get("is_open_access", False)),
                "abstract_text":  e.get("abstract_text") or "",
                "language":       e.get("language") or "",
                "affiliation":    e.get("affiliation") or "",
            })
        entries_df = pd.DataFrame.from_records(sanitized)
        if "pub_year" in entries_df.columns:
            entries_df["pub_year"] = pd.array(entries_df["pub_year"], dtype="Int64")

    # Build countries DataFrame
    if isinstance(raw_countries, dict):
        items = [{"country": k, "count": v} for k, v in raw_countries.items()]
        countries_df = pd.DataFrame.from_records(items)
    else:
        countries_df = pd.DataFrame()

    authors_df = pd.DataFrame()

    return entries_df, countries_df, authors_df, total_entries, citations, unique_authors_count, top_authors_data


def get_funding_agencies(limit: int = 50) -> dict:
    """
    Fetch top funding agencies and unique count from the backend.
    Returns {"agencies": [{"agency": str, "count": int}, ...], "total_unique": int}
    """
    try:
        params = {"limit": limit}
        resp = requests.get(api_constants.EPMC_FUNDING_AGENCIES, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Failed to fetch funding agencies: %s", exc)
        return {"agencies": [], "total_unique": 0}


def get_publication_types() -> list:
    """
    Fetch publication type counts from the backend.
    Returns [{"type": str, "count": int}, ...] — one entry per primary type,
    counts sum to total unique article count.
    """
    try:
        resp = requests.get(api_constants.EPMC_PUBLICATION_TYPES, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("types", []) if isinstance(data, dict) else []
    except Exception as exc:
        logger.warning("Failed to fetch publication types: %s", exc)
        return []


def compute_epmc_kpis(entries_df, citations_data, total_entries):
    """
    Derive summary KPIs from already-fetched EPMC data. No extra API calls.

    Returns a dict with:
      yoy_growth_pct  – publication growth % between the two most recent complete years
                        (None when fewer than two years of data exist)
      avg_citations   – mean citations per article, rounded to 1 dp
    """
    current_year = datetime.datetime.now().year

    # --- YoY publication growth ---
    yoy_growth_pct = None
    if not entries_df.empty and "pub_year" in entries_df.columns:
        yearly = (
            entries_df[entries_df["pub_year"].notna() & (entries_df["pub_year"] < current_year)]
            .groupby("pub_year")
            .size()
            .reset_index(name="count")
            .sort_values("pub_year")
        )
        if len(yearly) >= 2:
            prev  = int(yearly.iloc[-2]["count"])
            curr  = int(yearly.iloc[-1]["count"])
            if prev > 0:
                yoy_growth_pct = round((curr - prev) / prev * 100, 1)

    # --- Average citations per article ---
    # Sum cited_by_count from the already-deduplicated entries_df (1 row per article).
    # This avoids the inflated value from citations-over-years which counts duplicate
    # ingestion rows across the raw pmc_articles table.
    total_citations = 0
    if not entries_df.empty and "cited_by_count" in entries_df.columns:
        total_citations = int(entries_df["cited_by_count"].fillna(0).sum())
    avg_citations = round(total_citations / total_entries, 1) if total_entries > 0 else 0.0

    return {
        "yoy_growth_pct":   yoy_growth_pct,
        "avg_citations":    avg_citations,
        "total_citations":  total_citations,
    }

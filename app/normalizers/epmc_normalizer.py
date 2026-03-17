"""
Normalizer for raw EPMC API responses → clean pandas DataFrames.
Mirrors the pattern used by pypi_normalizer.py.
"""

import pandas as pd


def normalize_epmc_entries(raw_data):
    """
    Flatten the raw EPMC entries JSON into a pandas DataFrame.

    Args:
        raw_data (list[dict]): List of entry dicts from the API.

    Returns:
        pd.DataFrame: flattened DataFrame ready for DataTable.
    """
    if not raw_data:
        return pd.DataFrame()

    rows = []
    for item in raw_data:
        # chen needs to fix this – update the keys below to match the real API response
        rows.append({
            "pmcid": item.get("pmcid", ""),
            "title": item.get("title", ""),
            "author": item.get("author", ""),
            "journal": item.get("journal", ""),
            "publish_date": item.get("publish_date", ""),
            "affiliation_country": item.get("affiliation_country", ""),
        })

    return pd.DataFrame(rows)


def normalize_epmc_countries(raw_data):
    """
    Normalize country affiliation counts.

    Args:
        raw_data (list[dict]): e.g. [{"country": "US", "count": 42}, ...]

    Returns:
        pd.DataFrame with columns [country, count].
    """
    if not raw_data:
        return pd.DataFrame(columns=["country", "count"])

    # chen needs to fix this – update the key names to match the real API response
    df = pd.DataFrame.from_records(raw_data)
    return df


def normalize_epmc_authors(raw_data):
    """
    Normalize PMC author records.

    Args:
        raw_data (list[dict]): author records from the API.

    Returns:
        pd.DataFrame
    """
    if not raw_data:
        return pd.DataFrame()

    # chen needs to fix this – update the key names to match the real API response
    df = pd.DataFrame.from_records(raw_data)
    return df

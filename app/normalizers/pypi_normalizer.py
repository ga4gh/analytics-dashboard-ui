import pandas as pd

def normalize_pypi_packages(raw_data):
    """
    Flatten the raw PyPI API JSON into a pandas DataFrame.

    Args:
        raw_data (list[dict]): List of package dicts from API

    Returns:
        pd.DataFrame: flattened DataFrame ready for DataTable
    """
    if not raw_data:
        return pd.DataFrame()

    rows = []
    for item in raw_data:
        versions_count = 0
        if "versions" in item and item["versions"]:
            versions_count = item["versions"][0].get("versions", 0)

        rows.append({
            "project_name": item.get("project_name"),
            "description": item.get("description"),
            "author_name": item.get("author_name"),
            "author_email": item.get("author_email"),
            "category": item.get("category"),
            "versions_count": versions_count,
        })

    return pd.DataFrame(rows)

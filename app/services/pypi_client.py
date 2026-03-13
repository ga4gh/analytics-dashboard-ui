import requests
import app.constants.api as api_constants
import pandas as pd

def get_json(endpoint):
    """
    Function to get JSON response from API for get_json
    Args:
        endpoint (str): API endpoint URL
    Returns:
        dict: JSON response from the API
    """
    print(f"Calling API: {endpoint}")
    resp = requests.get(endpoint)
    resp.raise_for_status()
    return resp.json()

def get_all_packages():
    """
    Returns the full list of all PyPI package records stored in DB.
    Returns:
        List of dicts: [{"package": {obj...}, "version": {obj...}}, ...]
    """
    all_packages = get_json(api_constants.ALL_PACKAGES_API)
    all_packages_df = pd.DataFrame.from_records(all_packages)
    
    #print(all_packages_df)
    return all_packages

def get_total_packages():
    """
    Returns the total number of PyPI packages stored in DB.
    Returns:
        int: total number of packages
    """
    total_packages = get_json(api_constants.TOTAL_PACKAGES_API)
    total_packages = int(total_packages.get("total_packages", 0))
    return total_packages

def get_pypi_details():
    """
    Returns detailed metadata for each PyPI project.
    """
    pypi_details = get_json(api_constants.PYPI_DETAILS_API)
    #print(pypi_details)
    # Build DataFrame
    rows = []
    for pkg in pypi_details:
        versions_list = pkg.get("versions", [])
        versions_count = versions_list[0].get("versions", 0) if versions_list else 0
        rows.append({
            "project_name": pkg.get("project_name"),
            "description": pkg.get("description"),
            "author_name": pkg.get("author_name"),
            "author_email": pkg.get("author_email"),
            "category": pkg.get("category"),
            "versions_count": versions_count,
        })

    df = pd.DataFrame(rows)
    return df

def get_first_releases():
    """
    Returns the first release date for each PyPI project.
    """
    first_releases = get_json(api_constants.FIRST_RELEASES_API)
    return first_releases
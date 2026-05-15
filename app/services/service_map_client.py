import requests
import pandas as pd
from typing import Optional

BASE_URL = "https://implementation-registry.ga4gh.org/api"
STANDARDS_ENDPOINT = f"{BASE_URL}/standards"
SERVICES_ENDPOINT = f"{BASE_URL}/services"
DEPLOYMENTS_ENDPOINT = f"{BASE_URL}/deployments"

def get_json(endpoint: str, token: Optional[str] = None):
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"

    print(f"Calling API: {endpoint}")
    resp = requests.get(endpoint, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()

def prepare_service_map_data(fetch_date="2025-10-01"):
    standards_json = get_json(STANDARDS_ENDPOINT)
    services_json = get_json(SERVICES_ENDPOINT)
    deployments_json = get_json(DEPLOYMENTS_ENDPOINT)
    
    standards_df = pd.DataFrame.from_records(standards_json)
    services_df = pd.DataFrame.from_records(services_json)
    deployments_df = pd.DataFrame.from_records(deployments_json)

    return standards_df, services_df, deployments_df

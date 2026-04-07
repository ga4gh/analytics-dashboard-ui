import requests
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional

import app.constants.api as api_constants


def get_json(endpoint: str, token: Optional[str] = None, per_page: int = 100):
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"

    params = {"per_page": per_page, "page": 1}
    items = []
    url = endpoint

    while True:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if not isinstance(data, list):
            return data

        items.extend(data)

        if "next" in resp.links:
            url = resp.links["next"]["url"]
            params = None
        else:
            break

    return items


def prepare_github_data(fetch_date="2025-10-01"):
    GA4GH_json = get_json(api_constants.GITHUB_REPOS_API)

    gh_df = pd.DataFrame.from_records(GA4GH_json)

    gh_df["last_updated"] = pd.to_datetime(gh_df["last_updated"], utc=True, errors="raise")
    gh_df["pushed_at"] = pd.to_datetime(gh_df["pushed_at"], utc=True, errors="raise")
    gh_df["created_on"] = pd.to_datetime(gh_df["created_on"], utc=True, errors="raise")

    target_date = pd.to_datetime(fetch_date, utc=True)

    # Use absolute timedeltas so days-since values are never negative
    gh_df["days_since_pushed_at"] = (target_date - gh_df["pushed_at"]).abs().dt.days
    gh_df["days_since_last_updated"] = (target_date - gh_df["last_updated"]).abs().dt.days

    gh_df["activity_score"] = (
        1 / (1 + gh_df["days_since_pushed_at"])
        + 1 / (1 + gh_df["days_since_last_updated"])
    )

    # Top 15 active repos
    gh_activity_df = (
        gh_df.sort_values("activity_score", ascending=False)
        .head(15)
        .reset_index(drop=True)
    )

    # Activity status categories
    conditions = [
        (gh_df["is_archived"] == False) & (gh_df["days_since_pushed_at"] < 365),
        (gh_df["is_archived"] == False)
        & (gh_df["days_since_pushed_at"] >= 365)
        & (gh_df["days_since_pushed_at"] <= 1095),
        (gh_df["is_archived"] == False) & (gh_df["days_since_pushed_at"] > 1095),
        (gh_df["is_archived"] == True),
    ]
    choices = ["Active", "Moderate activity", "Inactive", "Archived"]

    gh_df["activity_status"] = np.select(conditions, choices, default="Unknown")

    gh_activity_counts = gh_df["activity_status"].value_counts().reset_index()
    gh_activity_counts.columns = ["Category", "Count"]
    
    gh_df['total_interest'] = gh_df['subscribers_count'] + gh_df['stargazers_count'] + gh_df['forks_count']
    gh_interest_df = gh_df.sort_values('total_interest', ascending=False).head(10).reset_index(drop=True)
    total_repositories = len(gh_df)
    
    workstreams = gh_df["workstream"].dropna().unique().tolist()

    return gh_df, gh_activity_df, gh_activity_counts, gh_interest_df, total_repositories, workstreams

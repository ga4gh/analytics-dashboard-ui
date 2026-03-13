#PubMed
from datetime import datetime

from app.constants.api import FIRST_RELEASES_API, GITHUB_REPOS_API, PM_KEYWORD, PYPI_DETAILS_API, TOTAL_PACKAGES_API
from app.services.github_client import get_json
import requests
import json
import dash
from typing import List, Optional, Dict, Any
from dash import Dash, dcc, html, Input, Output, callback, dash_table, jupyter_dash
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from collections import Counter
from datetime import datetime
import numpy as np

def get_last_year(dates):
    last_year = []
    for d in dates:
        if hasattr(d, "year"):
            y = d.year
        else:
            y = datetime.fromisoformat(d).year
        if y == 2025:
            last_year.append(d)
    return last_year

pubmed_json = get_json(PM_KEYWORD)
pm_df = pd.DataFrame.from_records(pubmed_json)
pm_df['publish_date'] = pd.to_datetime(pm_df['publish_date'], utc=True, errors='raise')
pm_df['year'] = pm_df['publish_date'].dt.year
pm_last_year = get_last_year(pm_df['publish_date'])

# GitHub
GA4GH_json = get_json(GITHUB_REPOS_API)
gh_df = pd.DataFrame.from_records(GA4GH_json)
gh_df['last_updated'] = pd.to_datetime(gh_df['last_updated'], utc=True, errors='raise')
gh_df['pushed_at'] = pd.to_datetime(gh_df['pushed_at'], utc=True, errors='raise')
gh_df['created_on'] = pd.to_datetime(gh_df['created_on'], utc=True, errors='raise')
gh_last_year = get_last_year(gh_df['created_on'])

# PyPi
pypi_packages_json = get_json(PYPI_DETAILS_API)
pypi_df = pd.DataFrame.from_records(pypi_packages_json)

pypi_first_versions_df = pd.DataFrame.from_records(get_json(FIRST_RELEASES_API))

pypi_df = pypi_df.merge(pypi_first_versions_df,how='inner',on='project_name')
assert pypi_df.shape[0] == int(get_json(TOTAL_PACKAGES_API).get("total_packages", 0))
pypi_df['first_release'] = pd.to_datetime(pypi_df['release_date'], utc=True, errors='raise')

pypi_last_year = get_last_year(pypi_df['first_release'])
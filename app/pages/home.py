# app/pages/home.py

from dash import html
import pandas as pd
import dash_bootstrap_components as dbc
from dash import register_page

from app.services.overview_client import (
    pm_df,
    gh_df,
    pypi_df,
)

# EPMC metrics
from app.services.epmc_client import prepare_epmc_data
from app.constants.constants import COUNTRIES_WHITELIST

# PyPI module
from app.layouts.pypi_layout import get_pypi_layout
from app.services.pypi_client import get_pypi_details, get_total_packages

# GitHub module
from app.layouts.github_layout import get_github_layout
from app.services.github_client import prepare_github_data

# EPMC module
from app.layouts.epmc_layout import get_epmc_layout

# Data tables layout (moved to bottom of page)
from app.layouts.datatables_layout import get_datatables_layout

# Prepare all EPMC data once (calls consolidated prepare_epmc_data which fetches all APIs in one pass)
(_epmc_entries_df, _epmc_countries_df, _epmc_authors_df, _epmc_total_entries, 
 _epmc_citations_df, _epmc_unique_authors, _epmc_top_authors_data) = prepare_epmc_data()

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

_epmc_total_citations = _count_citations_payload(_epmc_citations_df)
_epmc_article_count = _epmc_total_entries

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

_epmc_unique_countries, _epmc_countries_entries = _countries_stats_whitelist(_epmc_countries_df, COUNTRIES_WHITELIST)

# Prepare PyPI module data
_pypi_details = get_pypi_details()
_pypi_total = get_total_packages()

# Prepare GitHub module data
_gh_df, _, _, _, _gh_total = prepare_github_data()

# Build EPMC layout using consolidated data
_epmc_layout = get_epmc_layout(
    _epmc_entries_df,
    _epmc_countries_df,
    _epmc_authors_df,
    _epmc_total_entries,
    _epmc_citations_df,
)

# Prepare PyPI layout
_pypi_layout = get_pypi_layout(_pypi_details, _pypi_total)

# Prepare GitHub layout
_github_layout = get_github_layout(_gh_df, _gh_total)

register_page(
    __name__,
    path="/",
    title="GA4GH Analytics Dashboard",
    description="Welcome to the GA4GH Analytics Dashboard",
)

def indicator_card(value, label, color_class):
    return dbc.Card(
        dbc.CardBody(
            [
                html.H3(value, className="indicator-value"),
                html.Div(label, className="indicator-label"),
            ],
            className="indicator-card-body",
        ),
        className=f"indicator-card shadow-sm {color_class}",
    )

layout = dbc.Container(
    [

html.Div(
    [
        # ---------- TOP BAR ----------
dbc.Row(
    [
        dbc.Col(
            html.Img(
                src="/assets/logo-full-color.svg",
                className="logo-img",
            ),
            width="auto",
            className="logo-col",
        ),

        dbc.Col(
            html.Div(
                [
                    html.A("Overview", href="#overview", className="menu-link"),
                    html.A("EPMC", href="#epmc", className="menu-link"),
                    html.A("GitHub", href="#github", className="menu-link"),
                    html.A("PyPI", href="#pypi", className="menu-link"),
                    html.A("Tables", href="#tables", className="menu-link"),
                ],
                className="menu-container",
            ),
            className="menu-col d-flex justify-content-end",
        ),
    ],
    className="top-bar top-bar-row",  # 👈 add this
),

      # ---------- HERO ----------
html.Div(
    [
        html.Div(
            [
                html.H1(
                    "GA4GH Analytics Dashboard",
                    className="dashboard-title",
                ),

                html.P(
                    "The GA4GH Analytics Dashboard is a one-stop resource for understanding the real-world impact of GA4GH standards, policy frameworks, and products. Drawing on data from GitHub, PyPI, and PubMed, it tracks how GA4GH's work has been adopted, cited, and built upon across the genomics community.",
                    className="dashboard-summary",
                ),

                html.P(
                    "Whether you're a Work Stream contributor looking to understand how your efforts are landing, a product lead shaping the next development cycle, or a stakeholder making the case for genomic data sharing — this dashboard gives you the evidence to do it. Explore trends, spot",
                    className="dashboard-summary",
                ),
            ],
            className="hero-content-box",
        )
    ],
    className="hero-section",
    id="overview",
),
    ]
),

        html.Div(className="section-spacer"),

        # ---------- INFO BADGES ----------
        dbc.Row(
    [
        dbc.Col(
            dbc.Badge(
                "Data Updated: 2026-03-13",
                className="info-badge",
            ),
            width="auto",
        ),

        dbc.Col(
            dbc.Badge(
                "Created by: GA4GH Technical Team",
                className="info-badge",
            ),
            width="auto",
        ),

        dbc.Col(
            dbc.Badge(
                "Data Sources: GitHub, PyPI, Europe PMC",
                className="info-badge",
            ),
            width="auto",
        ),
    ],
    className="info-badges-row",
    align="center",
        ),

        # ---------- KPI INDICATORS ----------
dbc.Row(
    [
        dbc.Col(
            indicator_card(
                f"{_epmc_article_count:,}",
                "Europe PMC Publications",
                "border-red",
            ),
            md=2,
        ),

        dbc.Col(
            indicator_card(
                f"{_epmc_unique_authors:,}",
                "Total Authors",
                "border-orange",
            ),
            md=2,
        ),

        dbc.Col(
            indicator_card(
                f"{_epmc_total_citations:,}",
                "Total Citations",
                "border-green",
            ),
            md=2,
        ),

        dbc.Col(
            indicator_card(
                f"{_epmc_unique_countries:,}",
                "Total Countries",
                "border-lightblue",
            ),
            md=2,
        ),

        dbc.Col(
            indicator_card(
                f"{len(gh_df):,}",
                "GitHub Repositories",
                "border-darkblue",
            ),
            md=2,
        ),

        dbc.Col(
            indicator_card(
                f"{len(pypi_df):,}",
                "PyPI Packages",
                "border-purple",
            ),
            md=2,
        ),
    ],
    className="mb-4",
),
# ---------- MODULES ----------

html.Div(
    [
        html.Div(
            "European PMC (EPMC) Metrics",
            className="section-title",
        ),
        dbc.Row(
            [dbc.Col(_epmc_layout, md=12)],
            className="mt-4",
        ),
    ],
    id="epmc",
    className="epmc-section",
),

html.Div(
    [
        html.Div(
            "GitHub Metrics",
            className="section-title",
        ),
        dbc.Row(
            [dbc.Col(_github_layout, md=12)],
            className="mt-4",
        ),
    ],
    id="github",
    className="github-section",

),

html.Div(
    [
        html.Div(
            "PyPI Metrics",
            className="section-title",
        ),
        dbc.Row(
            [dbc.Col(_pypi_layout, md=12)],
            className="mt-4",
        ),
    ],
    id="pypi",
    className="pypi-section",
),

# ---------- TABLES ----------
html.Div(
    [
        html.Div(
            "Data Tables",
            className="section-title",
        ),

        html.Div(
            get_datatables_layout(
                _epmc_entries_df,
                _gh_df,
                _pypi_details,
            ),
            className="tables-container",
        ),
    ],
    id="tables",
    className="tables-section",
),

        # ---------- FOOTER ----------
        html.Div(
            "© 2026 GA4GH Analytics Dashboard",
            className="footer",
        ),
    ],
    fluid=True,
)
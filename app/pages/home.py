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
from app.services.epmc_client import (
    prepare_epmc_data,
    get_unique_citations,
    get_unique_authors_count,
    get_epmc_article_count,
)
from app.constants.constants import COUNTRIES_WHITELIST

# Prepare EPMC data once for the layout
_epmc_entries_df, _epmc_countries_df, _epmc_authors_df, _epmc_total_entries = prepare_epmc_data()

# Total unique authors: try common column names, fallback to first column
def _count_unique_authors(df):
    if df is None or df.empty:
        return 0
    cols = list(df.columns)
    # look for typical author column names
    for candidate in ("author", "name", "full_name", "author_name"):
        for c in cols:
            if c.lower() == candidate:
                return int(df[c].dropna().astype(str).nunique())
    # fallback: use first column
    return int(df.iloc[:, 0].dropna().astype(str).nunique())

_epmc_unique_authors = get_unique_authors_count()
_epmc_total_citations = get_unique_citations()
_epmc_article_count = get_epmc_article_count()

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

register_page(
    __name__,
    path="/",
    title="GA4GH Analytics Dashboard",
    description="Welcome to the GA4GH Analytics Dashboard",
)


def indicator_card(value, label, color, small=False):
    
    return dbc.Card(
        dbc.CardBody(
            [
                html.H3(
                    value,
                    style={
                        "margin": "0",
                        "fontSize": "26px",
                        "fontWeight": "600",
                        "color": "#2C3E50",
                    },
                ),
                html.Div(label, style={"fontSize": "14px", "color": "#77787B"}),
            ],
            style={"padding": "12px 16px"},
        ),
        style={
            "borderRadius": "10px",
            "border": "1px solid #E6E6E6",
            "borderRight": f"12px solid {color}",
            "height": "72px",
        },
        className="shadow-sm",
    )


layout = dbc.Container(
    [
        dbc.Row(
            [
                # ---------- LOGO ----------
                

                # ---------- TITLE ----------
                dbc.Col(
                    html.H1(
                        "GA4GH Analytics Dashboard",
                        style={
                            "fontSize": "56px",
                            "fontWeight": "700",
                            "color": "#2C3E50",
                            "marginBottom": "25px",
                            "marginTop": "30px",
                        },
                        className="text",
                    ),
                    md=9,
                    className="d-flex align-items-center",
                ),
                dbc.Col(
                    html.Img(
                        src="/assets/logo-full-color.svg",
                        style={
                            "width": "100%",
                            "maxHeight": "120px",
                            "objectFit": "contain",
                        },
                    ),
                    md=3,
                    className="d-flex align-items-center",
                ),
            ],
            align="center",
        ),

        

        # ---------- DESCRIPTION ----------
        dbc.Row(
            [



                dbc.Col(
                    [
                        html.P(
                            "Analytics are important for standards organisations like GA4GH "
                            "as it helps to make data-driven decisions. The GA4GH Tech Team "
                            "is building an analytics dashboard to enable our community to "
                            "quantify the impact of standards, policy frameworks and products "
                            "that have been actively developed over the last 12 years.",
                            style={
                                "fontSize": "18px",
                                "color": "#6C757D",
                                "lineHeight": "1.6",
                            },
                        ),

                        html.P(
                            "Collaborators across Work Streams can use this dashboard to "
                            "understand how their contributions advance genomic data sharing, "
                            "gather intelligence to guide future product development, and "
                            "identify implementation opportunities.",
                            style={
                                "fontSize": "18px",
                                "color": "#6C757D",
                                "lineHeight": "1.6",
                            },
                        ),
                    ],
                    md=8,
                ),

                

            ],
            align="center",
        ),

        html.Br(),

        # ---------- INFO BADGES ----------
        dbc.Row(
            [
                dbc.Col(
                    dbc.Badge(
                        "Data Updated: 2026-03-13",
                        color="light",
                        text_color="dark",
                        className="p-2",
                    ),
                    width="auto",
                ),

                dbc.Col(
                    dbc.Badge(
                        "Created by: GA4GH Technical Team",
                        color="light",
                        text_color="dark",
                        className="p-2",
                    ),
                    width="auto",
                ),

                dbc.Col(
                    dbc.Badge(
                        "Data Source: GitHub, PyPI, EuropePMC",
                        color="light",
                        text_color="dark",
                        className="p-2",
                    ),
                    width="auto",
                ),
            ],
            className="mb-4",
            align="center",
        ),

        # ---------- KPI INDICATORS ----------
            dbc.Row(
                [
                    dbc.Col(
                        indicator_card(
                                f"{_epmc_article_count:,}",
                                "EuropePMC Articles",
                                "#1B75BB",
                            ),
                        md=2,
                    ),

                    dbc.Col(
                        indicator_card(
                            f"{len(gh_df):,}",
                            "GitHub Repositories",
                            "#4FAEDC",
                        ),
                        md=2,
                    ),

                    dbc.Col(
                        indicator_card(
                            f"{len(pypi_df):,}",
                            "PyPI Packages",
                            "#FAA633",
                        ),
                        md=2,
                    ),

                    dbc.Col(
                        indicator_card(
                            f"{_epmc_unique_authors:,}",
                            "Total Authors",
                            "#7B2CBF",
                        ),
                        md=2,
                    ),

                    dbc.Col(
                        indicator_card(
                            f"{_epmc_total_citations:,}",
                            "Total Citations",
                            "#2ECC71",
                        ),
                        md=2,
                    ),

                    dbc.Col(
                        indicator_card(
                            f"{_epmc_unique_countries:,}",
                            "Total Countries",
                            "#E67E22",
                        ),
                        md=2,
                    ),
                ],
                className="mb-4",
            ),
    

        # ---------- MODULE CARDS ----------
        dbc.Row(
            [

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H3("PyPI Analytics"),
                                html.P("View package trends, categories, and versions"),
                                dbc.Button("Open", id="open-pypi", color="primary", size="lg"),
                            ]
                        ),
                        className="shadow-sm",
                        style={"textAlign": "center", "height": "250px"},
                    ),
                    md=4,
                ),

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H3("GitHub Analytics"),
                                html.P("Repository activity and metrics"),
                                dbc.Button("Open", id="open-github", color="success", size="lg"),
                            ]
                        ),
                        className="shadow-sm",
                        style={"textAlign": "center", "height": "250px"},
                    ),
                    md=4,
                ),

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H3("EPMC Analytics"),
                                html.P("Europe PMC entries, authors & affiliations"),
                                dbc.Button("Open", id="open-epmc", color="danger", size="lg"),
                            ]
                        ),
                        className="shadow-sm",
                        style={"textAlign": "center", "height": "250px"},
                    ),
                    md=4,
                ),

            ],
            justify="center",
        ),

        html.Br(),

        html.Div(id="module-content", style={"marginTop": "40px"}),

        # ---------- FOOTER ----------
        html.Div(
            "© 2026 GA4GH Analytics Dashboard",
            style={
                "textAlign": "center",
                "marginTop": "50px",
                "marginBottom": "50px",
                "color": "#95A5A6",
            },
        ),

    ],
    fluid=True,
)
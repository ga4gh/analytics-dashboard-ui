# app/pages/home.py

from dash import html
import pandas as pd
import dash_bootstrap_components as dbc
from dash import register_page

# EPMC metrics
from app.services.epmc_client import prepare_epmc_data
from app.constants.constants import COUNTRIES_WHITELIST

# PyPI module
from app.layouts.pypi_layout import get_pypi_layout
from app.services.pypi_client import get_pypi_details, get_total_packages, get_first_releases

# GitHub module
from app.layouts.github_layout import get_github_layout
from app.services.github_client import prepare_github_data

# EPMC module
from app.layouts.epmc_layout import get_epmc_layout
from app.layouts.combined_layout import get_combined_layout

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
_pypi_first_releases = pd.DataFrame.from_records(get_first_releases())

# Prepare GitHub module data
_gh_df, _, _, _, _gh_total, workstreams = prepare_github_data()

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
_github_layout = get_github_layout(_gh_df, _gh_total, workstreams)

# Prepare combined layout (GitHub + Europe PMC + PyPI)
_combined_layout = get_combined_layout(
    _gh_df,
    _epmc_entries_df,
    _pypi_first_releases,
)

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
                        "Data Updated: 2026-04-08",
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
                        "Data Sources: GitHub, PyPI, Europe PMC",
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

        # ---------- METHODS CARDS -----------
        html.Div(
                [
                    html.Div(
                            [
                                html.Span("▶ ", style={"fontSize": "12px", "marginRight": "4px"}),
                                html.Span("Show methods and terms "),
                                html.Span("▼", style={"fontSize": "12px"}),
                        ],
                        id="collapse-button",
                        n_clicks=0,
                        style={
                            "color": "#0d9cf0",
                            "cursor": "pointer",
                            "fontWeight": "600",
                            "fontSize": "16px",
                            "display": "inline-flex",
                            "alignItems": "center",
                            "gap": "4px",
                            "marginBottom": "1rem",
                        }
                    ),
                dbc.Collapse(
                    html.Div(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Card(
                                            dbc.CardBody(
                                                [
                                                    html.Span([
                                                        "This dashboard illustrates ",
                                                        html.Strong("GA4GH's overall ecosystem impact "),
                                                        "by bringing together three core dimensions of activity:"
                                                    ]),
                                                    html.Ol(
                                                        [
                                                            html.Li(
                                                                html.Span([
                                                                    "Scientific research and publications from ",
                                                                    html.Strong("PubMed Central (PMC)"),
                                                                ])
                                                            ),
                                                            html.Li(
                                                                html.Span([
                                                                    "Software development and implementation from ",
                                                                    html.Strong("GitHub")
                                                                ])
                                                            ),
                                                            html.Li(
                                                                html.Span([
                                                                    "Standards-enabled software distribution from ",
                                                                    html.Strong("PyPI")
                                                                ])
                                                            ),
                                                        ]
                                                    ),
                                                    html.Span([
                                                        "Rather than focusing on one platform in isolation, the following metrics, figures, and tables act as an executive snapshot of the full GA4GH value chain—from standards implementation, to community adoption, to scientific and clinical impact."
                                                    ]),
                                                ]
                                            )
                                        ),
                                    )
                                ],
                                style={"marginBottom": "20px"}
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Card(
                                            dbc.CardBody(
                                                [
                                                    html.H4("PubMed Central", className="card-title"),
                                                    html.H5("Methods", className="card-subtitle"),
                                                    html.Ul(
                                                        [
                                                            html.Li(
                                                                html.Span([
                                                                    "Article and citation data is collected from ",
                                                                    html.A("Europe PMC", href="https://europepmc.org/"),
                                                                    " via their ",
                                                                    html.A("Articles RESTful API", href="https://europepmc.org/RestfulWebService"),
                                                                    "."
                                                                ])
                                                            ),
                                                            html.Li("A list of GA4GH-related articles is constructed by searching the Europe PMC database for all articles that mention “GA4GH” or “Global Alliance for Genomics and Health.” Both published articles and preprints are considered."),
                                                            html.Li("For each article returned by the initial search, the following metrics are captured:"),
                                                            html.Ul(
                                                                [
                                                                    html.Li(
                                                                        html.Span([
                                                                            "The article's ",
                                                                            html.Strong("citation info"),
                                                                            " (i.e. authors, title, journal, publication date, volume and issue number, page numbers, DOI, etc.)"

                                                                        ]),
                                                                    ),
                                                                    html.Li(
                                                                        html.Span([
                                                                            "All instances in which the article was cited by another paper (i.e. ",
                                                                            html.Strong("citation"),
                                                                            ")"
                                                                        ])
                                                                    ),
                                                                    html.Li(
                                                                        html.Span([
                                                                            "The ",
                                                                            html.Strong("country affiliations"),
                                                                            " of all authors who contributed to the article"
                                                                        ])
                                                                    ),
                                                                ],
                                                                style={"listStyleType": "circle", "paddingLeft": "20px"},
                                                            ),
                                                            html.Li("Data tables and downstream figures are rebuilt on a regular cadence.")
                                                        ]
                                                    ),
                                                    html.H5("Terms", className="card-subtitle"),
                                                    html.Ul(
                                                        [
                                                            html.Li(
                                                                html.Span([
                                                                    html.Strong("GA4GH-related article:"),
                                                                    " A journal article that cites or mentions “GA4GH” or “Global Alliance for Genomics and Health.”"
                                                                ]),
                                                            ),
                                                            html.Li(
                                                                html.Span([
                                                                    html.Strong("GA4GH citation:"),
                                                                    " An instance in which any article in the Europe PMC database cites a GA4GH-related article.",
                                                                ]),
                                                            ),
                                                            html.Li(
                                                                html.Span([
                                                                    html.Strong("Country affiliation:"),
                                                                    " The country that an author is associated with, determined by their institutional affiliation."
                                                                ]),
                                                            )
                                                        ]
                                                    )
                                                ]
                                            )
                                        ),
                                    ),
                                    dbc.Col(
                                        dbc.Card(
                                            dbc.CardBody([
                                                html.H4("GitHub", className="card-title"),
                                                html.H5("Methods", className="card-subtitle"),
                                                html.Ul([
                                                    html.Li(
                                                        html.Span([
                                                            "Activity, usage, and contribution data is collected via ",
                                                            html.A("GitHub’s REST API", href="https://docs.github.com/en/rest"),
                                                            " for a curated list of repositories in the ",
                                                            html.A("ga4gh", href="https://github.com/ga4gh"),
                                                            " Github organization."
                                                        ]),
                                                    ),
                                                    html.Li("Each repository is enriched with metadata to allow for associations with the corresponding Work Stream."),
                                                    html.Li("For each repository, the following metrics are captured/calculated:"),
                                                    html.Ul(
                                                        [
                                                            html.Li(html.Strong("Activity score")),
                                                            html.Li(
                                                                html.Span([
                                                                    "Number of GitHub ",
                                                                    html.Strong("subscribers"),
                                                                ])
                                                            ),
                                                            html.Li(
                                                                html.Span([
                                                                    "Number of GitHub ",
                                                                    html.Strong("stargazers"),
                                                                ])
                                                            ),
                                                            html.Li(
                                                                html.Span([
                                                                    "Number of GitHub ",
                                                                    html.Strong("forks"),
                                                                ])
                                                            ),
                                                        ],
                                                        style={"listStyleType": "circle", "paddingLeft": "20px"},
                                                    ),
                                                    html.Li("Data tables and downstream figures are rebuilt on a regular cadence."),
                                                ]),
                                                html.H5("Terms", className="card-subtitle"),
                                                html.Ul([
                                                    html.Li(
                                                        html.Span([
                                                            html.Strong("Activity score:"),
                                                            " A calculated metric to indicate the level of activity in a GitHub repository, determined by the number of days since the most recent code push and repository update."
                                                        ])
                                                    ),
                                                    html.Li(
                                                        html.Span([
                                                            html.Strong("Subscriber:"),
                                                            " A GitHub user who receives notifications about activity (issues, pull requests, releases) for a particular repository, signaling deep interest or active participation in the repository."
                                                        ])
                                                    ),
                                                    html.Li(
                                                        html.Span([
                                                            html.Strong("Stargazer:"),
                                                            " A GitHub user who “stars” a particular repository, effectively bookmarking it."
                                                        ])
                                                    ),
                                                    html.Li(
                                                        html.Span([
                                                            html.Strong("Fork:"),
                                                            " A personal copy of a GA4GH repository to one's own workspace, signaling participation and experimentation with the codebase."
                                                        ])
                                                    ),
                                                ])
                                            ])
                                        ),
                                    ),
                                    dbc.Col(
                                        dbc.Card(
                                            dbc.CardBody([
                                                html.H4("PyPI", className="card-title"),
                                                html.H5("Methods", className="card-subtitle"),
                                                html.Ul([
                                                    html.Li(
                                                        html.Span([
                                                            "Package metadata is collected for a curated list of GA4GH-related software packages in the ",
                                                            html.A("Python Package Index (PyPI)", href="https://pypi.org/"),
                                                            ". Metadata is collected via the ",
                                                            html.A("PyPI REST API", href="https://docs.pypi.org/api/"),
                                                            "."
                                                        ]),
                                                    ),
                                                    html.Li("Each package is enriched with metadata to allow for associations with the corresponding Work Stream as well as package category (GA4GH Standard, GA4GH Mentions, Implementation)."),
                                                    html.Li("For each software package, the following metrics are captured:"),
                                                    html.Ul(
                                                        [
                                                            html.Li("Package metadata (name, description, authors, emails)"),
                                                            html.Li("Number of published versions"),
                                                        ],
                                                        style={"listStyleType": "circle", "paddingLeft": "20px"},
                                                    ),
                                                    html.Li("Data tables and downstream figures are rebuilt on a regular cadence."),
                                                ]),
                                                html.H5("Terms", className="card-subtitle"),
                                                html.Ul([
                                                    html.Li("Package categories:"),
                                                    html.Ul(
                                                        [
                                                            html.Li(
                                                                html.Span([
                                                                    html.Strong("GA4GH Standard:"),
                                                                    " PyPI package directly associated with a GA4GH specification, generally released as part of the standard itself."
                                                                ])
                                                            ),
                                                            html.Li(
                                                                html.Span([
                                                                    html.Strong("Implementation:"),
                                                                    " PyPI package that implements one or more GA4GH standards."
                                                                ])
                                                            ),
                                                            html.Li(
                                                                html.Span([
                                                                    html.Strong("GA4GH Mentions:"),
                                                                    " PyPI package that references and/or impacts the GA4GH ecosystem but does not directly adopt any GA4GH standards."
                                                                ])
                                                            ),
                                                        ],
                                                        style={"listStyleType": "circle", "paddingLeft": "20px"},
                                                    ),
                                                ]),
                                            ]),
                                        ),
                                    ),
                                ],
                                style={"marginBottom": "20px"}
                            ),
                        ],
                    ),
                    id="collapse",
                    is_open=False,
                ),
            ]
        ),

        # ---------- KPI INDICATORS ----------
        dbc.Row(
            [
                dbc.Col(
                    indicator_card(
                            f"{_epmc_article_count:,}",
                            "Europe PMC Publications",
                            "#1B75BB",
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
                        f"{_epmc_citations_df.get('total_citations', 0):,}",
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

                dbc.Col(
                    indicator_card(
                        f"{_gh_total:,}",
                        "GitHub Repositories",
                        "#4FAEDC",
                    ),
                    md=2,
                ),

                dbc.Col(
                    indicator_card(
                        f"{_pypi_total:,}",
                        "PyPI Packages",
                        "#FAA633",
                    ),
                    md=2,
                ),
               
            ],
            className="mb-4",
        ),
            
        # ---------- MODULE CONTENT (Summary Charts & Graphs) ----------
        dbc.Row([dbc.Col(_combined_layout, md=12)], className="mt-4"),
        dbc.Row([dbc.Col(_epmc_layout, md=12)], className="mt-4"),
        dbc.Row([dbc.Col(_github_layout, md=12)], className="mt-4"),
        dbc.Row([dbc.Col(_pypi_layout, md=12)], className="mt-4"),

        # ---------- DATA TABLES (at bottom) ----------
        get_datatables_layout(
            _epmc_entries_df,
            _gh_df,
            _pypi_details,
        ),
        
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
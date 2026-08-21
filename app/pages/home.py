# app/pages/home.py

from dash import html, dcc
import pandas as pd
import dash_bootstrap_components as dbc
from dash import register_page

# EPMC metrics
from app.services.epmc_client import prepare_epmc_data, _countries_stats_whitelist, compute_epmc_kpis, get_funding_agencies, get_publication_types
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

# Service Map module
from app.layouts.service_map_layout import get_service_map_layout
from app.services.service_map_client import prepare_service_map_data

# Data tables layout (moved to bottom of page)
from app.layouts.datatables_layout import get_datatables_layout

# Persona layout components
from app.layouts.funder_layout import get_publication_charts_section, get_funder_only_charts_section
from app.callbacks.epmc_callbacks import fig_epmc_countries_choropleth
from app.layouts.researcher_layout import get_researcher_charts_section
from app.layouts.developer_layout import get_developer_charts_section
from app.layouts.community_layout import get_community_charts_section
from app.services.summary_client import get_summary_overview

# Prepare all EPMC data once (calls consolidated prepare_epmc_data which fetches all APIs in one pass)
(_epmc_entries_df, _epmc_countries_df, _epmc_authors_df, _epmc_total_entries,
 _epmc_citations_df, _epmc_unique_authors, _epmc_top_authors_data) = prepare_epmc_data()

_epmc_article_count = _epmc_total_entries

_epmc_unique_countries, _epmc_countries_entries = _countries_stats_whitelist(_epmc_countries_df, COUNTRIES_WHITELIST)

_epmc_kpis = compute_epmc_kpis(_epmc_entries_df, _epmc_citations_df, _epmc_total_entries)
_epmc_yoy_growth_pct   = _epmc_kpis["yoy_growth_pct"]
_epmc_avg_citations    = _epmc_kpis["avg_citations"]
_epmc_total_citations  = _epmc_kpis["total_citations"]

_epmc_funding_data     = get_funding_agencies(limit=50)
_epmc_pub_types        = get_publication_types()

# Yearly publication counts for interactive YoY KPI card
import datetime as _dt
_current_year = _dt.datetime.now().year
if not _epmc_entries_df.empty and "pub_year" in _epmc_entries_df.columns:
    _yearly_pub_counts = {
        int(k): int(v)
        for k, v in _epmc_entries_df[
            _epmc_entries_df["pub_year"].notna() & (_epmc_entries_df["pub_year"] < _current_year)
        ].groupby("pub_year").size().items()
    }
else:
    _yearly_pub_counts = {}
_yoy_year_options = [{"label": str(y), "value": y} for y in sorted(_yearly_pub_counts.keys())]
_yoy_default_year = max(_yearly_pub_counts.keys()) if _yearly_pub_counts else None

# Open Access rate — computed from entries_df (no extra API needed)
if not _epmc_entries_df.empty and "is_open_access" in _epmc_entries_df.columns:
    _oa_count = int(_epmc_entries_df["is_open_access"].sum())
    _oa_rate  = round(_oa_count / len(_epmc_entries_df) * 100, 1)
else:
    _oa_count = 0
    _oa_rate  = 0.0

# Prepare PyPI module data
_pypi_details = get_pypi_details()
_pypi_total = get_total_packages()
_pypi_first_releases = pd.DataFrame.from_records(get_first_releases())

# Prepare GitHub module data
_gh_df, _, _, _gh_interest_df, _gh_total, workstreams = prepare_github_data()

# Prepare Service Map module data
standards_df, services_df, deployments_df = prepare_service_map_data()

# Build EPMC layout using consolidated data
_epmc_layout = get_epmc_layout(
    _epmc_entries_df,
    _epmc_countries_df,
    _epmc_authors_df,
    _epmc_total_entries,
    _epmc_citations_df,
)

# Build persona chart components
_agencies_list = _epmc_funding_data.get("agencies", []) if isinstance(_epmc_funding_data, dict) else []
_funding_bodies_count = _epmc_funding_data.get("total_unique", 0) if isinstance(_epmc_funding_data, dict) else 0

_choropleth_fig      = fig_epmc_countries_choropleth(_epmc_countries_df)
_publication_charts  = get_publication_charts_section(_epmc_entries_df, _choropleth_fig)
_funder_only_charts  = get_funder_only_charts_section(_agencies_list)
_researcher_charts   = get_researcher_charts_section(_epmc_entries_df, _epmc_pub_types)
_developer_charts    = get_developer_charts_section(_gh_df, _pypi_first_releases.to_dict("records") if not _pypi_first_releases.empty else [], services_df)
_summary_overview    = get_summary_overview()
_community_charts    = get_community_charts_section(_gh_df, _gh_interest_df)

# Prepare PyPI layout
_pypi_layout = get_pypi_layout(_pypi_details, _pypi_total)

# Prepare GitHub layout
_github_layout = get_github_layout(_gh_df, _gh_total, workstreams)

# Prepare combined layout (GitHub + Europe PMC + PyPI)
_combined_layout = get_combined_layout(
    _gh_df,
    _epmc_entries_df,
    _pypi_first_releases,
    _epmc_citations_df,
)

# Prepare service map layout
_service_map_layout = get_service_map_layout(standards_df, services_df, deployments_df)

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
            html.A(
                html.Span(
                    [
                        html.Img(
                            src="/assets/logo-mark-color.svg",
                            alt="The Global Alliance for Genomics and Health",
                            className="brand-logo-img",
                        ),
                        html.Span("GA4GH", className="brand-text-primary"),
                        html.Span("Analytics Dashboard", className="brand-text-base"),
                    ],
                    className="brand-lockup",
                ),
                href="/",
                className="brand-link",
            ),
            width="auto",
            className="logo-col",
        ),

        dbc.Col(
            html.Div(
                [
                    html.A("Overview", href="#overview", className="menu-link"),
                    html.A("Service Map", href="#servicemap", className="menu-link", id="navlink-servicemap"),
                    html.A("Cumulative Metrics", href="#metrics", className="menu-link"),
                    html.A("EPMC", href="#epmc", className="menu-link", id="navlink-epmc"),
                    html.A("Publications", href="#publication-charts", className="menu-link", id="navlink-publication-charts"),
                    html.A("Funding", href="#funder-only-charts", className="menu-link", id="navlink-funder-only-charts"),
                    html.A("Research", href="#researcher-charts", className="menu-link", id="navlink-researcher-charts"),
                    html.A("GitHub", href="#github", className="menu-link", id="navlink-github"),
                    html.A("PyPI", href="#pypi", className="menu-link", id="navlink-pypi"),
                    html.A("Developer", href="#developer-charts", className="menu-link", id="navlink-developer-charts"),
                    html.A("Community", href="#community-charts", className="menu-link", id="navlink-community-charts"),
                    html.A("Tables", href="#tables", className="menu-link", id="navlink-tables"),
                ],
                className="menu-container",
            ),
            className="menu-col d-flex justify-content-end",
        ),
    ],
    className="top-bar top-bar-row",  # 👈 add this
),

      # ---------- HERO ----------
      # Matches new_ga4gh's layout/_page-heroes.scss `.page-hero-standard-wrapper.none`
      # (the neutral grey/logo treatment used by standard pages with no work-stream section)
html.Div(
    html.Div(
        html.Div(
            [

                html.H1(
                    "GA4GH Analytics Dashboard",
                    className="dashboard-title",
                ),

                html.P(
                    "The GA4GH Analytics Dashboard is a one-stop resource for understanding the real-world impact of GA4GH standards, policy frameworks, and products. Drawing on data from GitHub, PyPI, and Europe PMC, it tracks how GA4GH's work has been adopted, cited, and built upon across the genomics community.",
                    className="dashboard-summary",
                ),

                html.P(
                    "Whether you're a Work Stream contributor looking to understand how your efforts are landing, a product lead shaping the next development cycle, or a stakeholder making the case for genomic data sharing — this dashboard gives you the evidence to do it. Explore trends, spot implementation gaps, and see over a decade of open science translated into data.",
                    className="dashboard-summary",
                ),

                # ---------- INFO BADGES ----------
                html.Div(
                    [
                        dbc.Badge("Created by: GA4GH Technical Team", className="hero-badge"),
                        dbc.Badge("Data Sources: GitHub, PyPI, Europe PMC, Implementation Registry", className="hero-badge"),
                    ],
                    className="hero-badges-row",
                ),

                # ---------- DATA UPDATED BADGES (own row) ----------
                html.Div(
                    [
                        dbc.Badge("Data Updated:", className="hero-badge"),
                        dbc.Badge(
                            f"Europe PMC: {(_summary_overview or {}).get('epmc', {}).get('last_ingested') or 'N/A'}",
                            className="hero-badge",
                        ),
                        dbc.Badge(
                            f"GitHub: {(_summary_overview or {}).get('github', {}).get('last_ingested') or 'N/A'}",
                            className="hero-badge",
                        ),
                         dbc.Badge(
                            f"PyPI: {(_summary_overview or {}).get('pypi', {}).get('last_ingested') or 'N/A'}",
                            className="hero-badge",
                        ),
                    ],
                    className="hero-badges-row",
                ),
            ],
            className="hero-summary",
        ),
        className="hero-standard",
    ),
    className="hero-section",
    id="overview",
),
    ]
),

        html.Div(className="section-spacer"),

        dcc.Store(id="active-persona", storage_type="session", data="default"),
        dcc.Store(id="yearly-pub-counts", data=_yearly_pub_counts),

        # ---------- METHODS CARDS -----------
        html.Div(
                [
                    html.Div(
                            [
                                html.Span("Show methods and terms "),
                                html.Span(className="methods-toggle-chevron"),
                        ],
                        id="collapse-button",
                        n_clicks=0,
                        className="methods-toggle",
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
                                                                    html.Strong("Europe PMC"),
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
                                                ],
                                                className="methods-card-body"
                                            )
                                        ),
                                    )
                                ],
                                className="methods-intro-row",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Card(
                                            dbc.CardBody(
                                                [
                                                    html.H4("Europe PMC", className="card-title"),
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
                                                                className="circle-sublist",
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
                                                ],
                                                className="methods-card-body"
                                            ),
                                            className="h-100 w-100",
                                        ),
                                        className="d-flex",
                                    ),
                                    dbc.Col(
                                        dbc.Card(
                                            dbc.CardBody(
                                                [
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
                                                        className="circle-sublist",
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
                                            ],
                                                className="methods-card-body"
                                            ),
                                            className="h-100 w-100",
                                        ),
                                        className="d-flex",
                                    ),
                                    dbc.Col(
                                        dbc.Card(
                                            dbc.CardBody(
                                                [
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
                                                        className="circle-sublist",
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
                                                        className="circle-sublist",
                                                    ),
                                                ]),
                                            ],
                                                className="methods-card-body"
                                            ),
                                            className="h-100 w-100",
                                        ),
                                        className="d-flex",
                                    ),
                                ],
                                className="methods-cards-row mb-4",
                            ),
                        ],
                    ),
                    id="collapse",
                    is_open=False,
                ),
            ],
            className="section-standard-width",
        ),

        # ---------- PERSONA SELECTOR ----------
        html.Div(
            [
                html.Span("View as:", className="persona-selector-label"),
                html.Div(
                    [
                        dbc.Button("Default",        id="persona-btn-default",    n_clicks=0, color="primary", outline=False, className="persona-btn active-persona"),
                        dbc.Button("Funder",         id="persona-btn-funder",     n_clicks=0, color="primary", outline=True,  className="persona-btn"),
                        dbc.Button("Researcher",     id="persona-btn-researcher", n_clicks=0, color="primary", outline=True,  className="persona-btn"),
                        dbc.Button("Developer",      id="persona-btn-developer",  n_clicks=0, color="primary", outline=True,  className="persona-btn"),
                        dbc.Button("GA4GH Community", id="persona-btn-community", n_clicks=0, color="primary", outline=True,  className="persona-btn"),
                    ],
                    className="persona-btn-group",
                ),
            ],
            className="persona-selector-row",
        ),

        # ---------- KPI INDICATORS ----------
        # Order: Publications → Citations → Authors → Countries → GitHub → PyPI
        # Funder/researcher-specific KPIs are interspersed and hidden by default
        dbc.Row(
            [
                # --- Publications group ---
                dbc.Col(
                    indicator_card(
                        f"{_epmc_article_count:,}",
                        "Europe PMC Publications",
                        "border-red",
                    ),
                    md=2,
                    id="kpi-publications",
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.Div([
                                html.H3(id="yoy-growth-value", className="indicator-value yoy-value-heading"),
                                dcc.Dropdown(
                                    id="yoy-year-selector",
                                    options=_yoy_year_options,
                                    value=_yoy_default_year,
                                    clearable=False,
                                    className="yoy-year-dropdown",
                                ),
                            ], className="yoy-header-row"),
                            html.Div("YoY Publication Growth", className="indicator-label"),
                        ], className="yoy-card-body"),
                        className="indicator-card shadow-sm border-pink",
                    ),
                    md=2,
                    id="funder-kpi-yoy",
                    style={"display": "none"},
                ),
                # --- Citations group ---
                dbc.Col(
                    indicator_card(
                        f"{_epmc_total_citations:,}",
                        "Total Citations",
                        "border-orange",
                    ),
                    md=2,
                    id="kpi-citations",
                ),
                dbc.Col(
                    indicator_card(
                        str(_epmc_avg_citations),
                        "Avg Citations / Paper",
                        "border-secondary-orange",
                    ),
                    md=2,
                    id="funder-kpi-avg-citations",
                    style={"display": "none"},
                ),
                # --- Authors group ---
                dbc.Col(
                    indicator_card(
                        f"{_epmc_unique_authors:,}",
                        "Total Authors",
                        "border-lightblue",
                    ),
                    md=2,
                    id="kpi-authors",
                ),
                dbc.Col(
                    indicator_card(
                        f"{_epmc_unique_countries:,}",
                        "Total Countries",
                        "border-darkblue",
                    ),
                    md=2,
                    id="kpi-countries",
                ),
                # --- GitHub / PyPI group ---
                dbc.Col(
                    indicator_card(
                        f"{_gh_total:,}",
                        "GitHub Repositories",
                        "border-green",
                    ),
                    md=2,
                    id="kpi-github",
                ),
                dbc.Col(
                    indicator_card(
                        f"{_pypi_total:,}",
                        "PyPI Packages",
                        "border-purple",
                    ),
                    md=2,
                    id="kpi-pypi",
                ),
                # --- Researcher-specific KPIs — hidden by default ---
                dbc.Col(
                    indicator_card(
                        f"{_oa_rate}%",
                        "Open Access Rate",
                        "border-darkgreen",
                    ),
                    md=2,
                    id="researcher-kpi-open-access",
                    style={"display": "none"},
                ),
            ],
            className="mb-4 gy-3 section-standard-width kpi-row",
        ),

        # ---------- MODULE CONTENT (Summary Charts & Graphs) ----------

html.Div(
    [
        html.Div(
            "Service Map",
            className="section-title",
        ),
        dbc.Row(
            [dbc.Col(_service_map_layout, md=12)],
        ),
    ],
    id="servicemap",
    className="servicemap-section",
),

html.Div(
    [
        html.Div(
            "Cumulative Metrics",
            className="section-title",
        ),
        dbc.Row(
            [dbc.Col(_combined_layout, md=12)],
        ),
    ],
    id="metrics",
    className="metrics-section",
),

html.Div(
    [
        html.Div(
            "European PMC (EPMC) Metrics",
            className="section-title",
        ),
        dbc.Row(
            [dbc.Col(_epmc_layout, md=12)],
        ),
    ],
    id="epmc",
    className="epmc-section",
),

_publication_charts,
_funder_only_charts,
_researcher_charts,

html.Div(
    [
        html.Div(
            "GitHub Metrics",
            className="section-title",
        ),
        dbc.Row(
            [dbc.Col(_github_layout, md=12)],
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
        ),
    ],
    id="pypi",
    className="pypi-section",
),

_developer_charts,

_community_charts,

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

# ---------- CHART EXPAND MODAL ----------
# Single shared modal for every chart's "expand" button (see
# chart_expand_button() in ga4gh_theme.py) — assets/chart_modal.js clones
# the clicked chart's live Plotly data/layout straight from the DOM into
# #chart-modal-graph, so this never needs a Dash callback or per-chart
# wiring. Styled in style.css to match new_ga4gh's own _image-modal.scss.
html.Div(
    [
        html.Button(
            "×",
            className="chart-modal-close-trigger",
            **{"aria-label": "Close"},
        ),
        html.Div(
            html.Div(
                [
                    html.Div(id="chart-modal-graph"),
                    html.Div(id="chart-modal-caption", className="chart-modal-caption"),
                ],
                className="chart-modal-content-inner",
            ),
            className="chart-modal-content",
        ),
    ],
    id="chart-modal",
    className="chart-modal",
),

    ],
    fluid=True,
)
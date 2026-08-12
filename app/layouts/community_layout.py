import pandas as pd
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import dcc, html

from app.layouts.combined_layout import _build_source_year_df


# ---------------------------------------------------------------------------
# Figure builders
# ---------------------------------------------------------------------------

_SOURCE_COLORS = {
    "Publications": "#1b75bb",
    "GitHub Repos": "#2a9d8f",
    "PyPI Packages": "#6a4c93",
}


def _cross_source_growth_figure(
    epmc_df: pd.DataFrame,
    gh_df: pd.DataFrame,
    pypi_first_releases_df: pd.DataFrame,
) -> go.Figure:
    """
    Cumulative growth of EPMC publications, GitHub repos, and PyPI packages
    on a single timeline — one line per source.
    """
    epmc_year_df = _build_source_year_df(epmc_df, "pub_year", "title", "Publications")

    gh_source = gh_df.copy() if gh_df is not None and not gh_df.empty else pd.DataFrame()
    if not gh_source.empty and "created_on" in gh_source.columns:
        gh_source["created_year"] = pd.to_datetime(
            gh_source["created_on"], errors="coerce", utc=True
        ).dt.year
        gh_source["repo_name"] = gh_source.get("name", gh_source.index.astype(str))
        gh_year_df = _build_source_year_df(gh_source, "created_year", "repo_name", "GitHub Repos")
    else:
        gh_year_df = pd.DataFrame(columns=["year", "item", "Source"])

    pypi_source = pypi_first_releases_df.copy() if pypi_first_releases_df is not None and not pypi_first_releases_df.empty else pd.DataFrame()
    if not pypi_source.empty and "release_date" in pypi_source.columns:
        pypi_source["release_year"] = pd.to_datetime(
            pypi_source["release_date"], errors="coerce", utc=True
        ).dt.year
        pypi_year_df = _build_source_year_df(pypi_source, "release_year", "project_name", "PyPI Packages")
    else:
        pypi_year_df = pd.DataFrame(columns=["year", "item", "Source"])

    fig = go.Figure()

    for source_df, source_name in [
        (epmc_year_df, "Publications"),
        (gh_year_df, "GitHub Repos"),
        (pypi_year_df, "PyPI Packages"),
    ]:
        if source_df.empty:
            continue
        yearly = (
            source_df.groupby("year", as_index=False)
            .agg(count=("item", "count"))
            .sort_values("year")
        )
        yearly["cumulative"] = yearly["count"].cumsum()
        color = _SOURCE_COLORS[source_name]
        fig.add_trace(go.Scatter(
            x=yearly["year"],
            y=yearly["cumulative"],
            mode="lines+markers",
            name=source_name,
            line={"color": color, "width": 2},
            marker={"color": color, "size": 6},
            hovertemplate=f"{source_name}<br>Year: %{{x}}<br>New this year: %{{customdata}}<br>Total to date: %{{y}}<extra></extra>",
            customdata=yearly["count"],
        ))

    fig.update_layout(
        template="simple_white",
        height=420,
        margin={"l": 40, "r": 20, "t": 30, "b": 50},
        xaxis={"title": "Year", "tickmode": "linear", "dtick": 2},
        yaxis={"title": "Cumulative Count"},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    )
    return fig


def _freshness_panel(freshness_data: dict | None, epmc_count: int, gh_count: int, pypi_count: int):
    """
    Data freshness summary panel. Uses real last_ingested timestamps when
    freshness_data is provided by the backend /summary/overview endpoint;
    falls back to 'Pending' until that endpoint is available.
    """
    def _last(key):
        if freshness_data and key in freshness_data:
            return freshness_data[key].get("last_ingested", "Pending")
        return "Pending"

    rows = [
        ("Europe PMC",  epmc_count,  _last("epmc"),   "#1b75bb"),
        ("GitHub",      gh_count,    _last("github"),  "#2a9d8f"),
        ("PyPI",        pypi_count,  _last("pypi"),    "#6a4c93"),
    ]

    cards = []
    for label, count, last_ingested, color in rows:
        cards.append(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.Div(label, style={"fontWeight": "600", "fontSize": "14px", "color": color}),
                        html.H4(f"{count:,}", style={"margin": "4px 0"}),
                        html.Div(
                            [html.Span("Last ingested: ", style={"color": "#888", "fontSize": "12px"}),
                             html.Span(last_ingested, style={"fontSize": "12px"})],
                        ),
                    ]),
                    className="shadow-sm",
                    style={"borderRadius": "12px", "borderTop": f"3px solid {color}"},
                ),
                md=4,
            )
        )
    return dbc.Row(cards, className="mb-4")


# ---------------------------------------------------------------------------
# Public layout builder
# ---------------------------------------------------------------------------

def get_community_charts_section(
    epmc_df: pd.DataFrame,
    gh_df: pd.DataFrame,
    pypi_first_releases_df: pd.DataFrame,
    epmc_count: int,
    gh_count: int,
    pypi_count: int,
    freshness_data: dict | None = None,
):
    """
    GA4GH Community charts: cross-source cumulative growth and data freshness panel.
    Hidden by default; persona callback sets display:block.
    """
    fig_growth = _cross_source_growth_figure(epmc_df, gh_df, pypi_first_releases_df)

    return html.Div(
        [
            html.Div("GA4GH Community Overview", className="section-title"),

            # Data freshness panel
            _freshness_panel(freshness_data, epmc_count, gh_count, pypi_count),

            # Cross-source growth chart
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            html.Figure([
                                html.H5("Cumulative Growth by Source",
                                        style={"marginBottom": "8px"}),
                                dcc.Graph(
                                    id="community-cross-source-growth",
                                    figure=fig_growth,
                                    config={"displayModeBar": False},
                                ),
                                html.Figcaption(
                                    "Cumulative count of GA4GH publications (Europe PMC), repositories (GitHub), and packages (PyPI) over time.",
                                    style={"fontSize": "13px", "color": "#777", "marginTop": "6px"},
                                ),
                            ])
                        ),
                        className="mb-4 shadow-sm",
                        style={"borderRadius": "12px"},
                    ),
                    width=12,
                ),
            ),
        ],
        id="community-charts",
        style={"display": "none"},
        className="epmc-section",
    )

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import dcc, html

from app.utils.ga4gh_theme import WORKSTREAM_COLORS, COLORS


# ---------------------------------------------------------------------------
# Figure builders
# ---------------------------------------------------------------------------

def _repos_by_workstream_figure(gh_df: pd.DataFrame) -> go.Figure:
    if gh_df is None or gh_df.empty or "workstream" not in gh_df.columns:
        return go.Figure().update_layout(title="No workstream data available")

    ws = (
        gh_df["workstream"]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
    )
    counts = ws.value_counts().reset_index()
    counts.columns = ["workstream", "count"]
    counts = counts.sort_values("count", ascending=True)
    bar_colors = counts["workstream"].map(WORKSTREAM_COLORS).fillna(COLORS["darkblue"])

    fig = px.bar(
        counts,
        x="count",
        y="workstream",
        orientation="h",
        labels={"count": "Repositories", "workstream": "Work Stream"},
        template="simple_white",
    )
    fig.update_traces(marker_color=bar_colors, hovertemplate="%{y}<br>Repos: %{x}<extra></extra>")
    fig.update_layout(
        height=420,
        margin={"l": 10, "r": 20, "t": 30, "b": 50},
        xaxis={"title": "Number of Repositories", "showgrid": True, "gridcolor": COLORS["lightgrey"]},
        yaxis={"title": "", "automargin": True},
        hoverlabel=dict(font_color="white"),
    )
    return fig


def _pypi_releases_per_year_figure(first_releases: list) -> go.Figure:
    if not first_releases:
        return go.Figure().update_layout(title="No PyPI release data available")

    df = pd.DataFrame(first_releases)
    if "release_date" not in df.columns:
        return go.Figure().update_layout(title="No release date data available")

    df["release_year"] = pd.to_datetime(df["release_date"], errors="coerce", utc=True).dt.year
    yearly = (
        df.dropna(subset=["release_year"])
        .groupby("release_year")
        .size()
        .reset_index(name="count")
        .sort_values("release_year")
    )
    yearly["release_year"] = yearly["release_year"].astype(int)

    fig = px.bar(
        yearly,
        x="release_year",
        y="count",
        labels={"release_year": "Year", "count": "Packages"},
        template="simple_white",
        color_discrete_sequence=[COLORS["purple"]],
    )
    fig.update_traces(hovertemplate="Year: %{x}<br>Packages: %{y}<extra></extra>")
    fig.update_layout(
        height=380,
        margin={"l": 40, "r": 20, "t": 30, "b": 50},
        xaxis={"tickmode": "linear", "dtick": 1, "title": "Year"},
        yaxis={"title": "New Packages Released", "showgrid": True, "gridcolor": COLORS["lightgrey"]},
        bargap=0.25,
        hoverlabel=dict(font_color="white"),
    )
    return fig


def _standards_service_count_figure(services_df: pd.DataFrame) -> go.Figure:
    if services_df is None or services_df.empty:
        return go.Figure().update_layout(title="No implementation registry data available")

    if "standardVersion" not in services_df.columns:
        return go.Figure().update_layout(title="Missing standardVersion column")

    abbr_series = (
        services_df["standardVersion"]
        .apply(lambda v: v.get("ga4ghProduct") if isinstance(v, dict) else None)
        .dropna()
        .astype(str)
    )
    counts = abbr_series.value_counts().reset_index()
    counts.columns = ["standard", "services"]
    counts = counts.sort_values("services", ascending=True)

    fig = px.bar(
        counts,
        x="services",
        y="standard",
        orientation="h",
        labels={"services": "Registered Services", "standard": "GA4GH Standard"},
        template="simple_white",
        color_discrete_sequence=[COLORS["darkblue"]],
    )
    fig.update_traces(hovertemplate="%{y}<br>Services: %{x}<extra></extra>")
    fig.update_layout(
        height=420,
        margin={"l": 10, "r": 20, "t": 30, "b": 50},
        xaxis={"title": "Number of Registered Services", "showgrid": True, "gridcolor": COLORS["lightgrey"]},
        yaxis={"title": "", "automargin": True},
        hoverlabel=dict(font_color="white"),
    )
    return fig


# ---------------------------------------------------------------------------
# Public layout builder
# ---------------------------------------------------------------------------

def get_developer_charts_section(gh_df: pd.DataFrame, first_releases: list,
                                  services_df: pd.DataFrame):
    """
    Developer-specific charts: GitHub repos by workstream, PyPI releases per year,
    GA4GH standards by service count.
    Hidden by default; persona callback sets display:block.
    """
    fig_workstream = _repos_by_workstream_figure(gh_df)
    fig_pypi       = _pypi_releases_per_year_figure(first_releases)
    fig_standards  = _standards_service_count_figure(services_df)

    return html.Div(
        [
            html.Div("Developer Analytics", className="section-title"),

            # Row 1: GitHub repos by workstream + PyPI releases per year
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                html.Figure([
                                    html.H5("GitHub Repositories by Work Stream",
                                            style={"marginBottom": "8px"}),
                                    dcc.Graph(
                                        id="dev-repos-by-workstream",
                                        figure=fig_workstream,
                                        config={"displayModeBar": False},
                                    ),
                                    html.Figcaption(
                                        "Count of GA4GH GitHub repositories grouped by Work Stream.",
                                        style={"color": COLORS["grey"], "marginTop": "6px"},
                                    ),
                                ])
                            ),
                            className="shadow-sm h-100 w-100",
                            style={"borderRadius": "12px"},
                        ),
                        className="d-flex",
                        md=6,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                html.Figure([
                                    html.H5("PyPI Packages Released Per Year",
                                            style={"marginBottom": "8px"}),
                                    dcc.Graph(
                                        id="dev-pypi-releases-per-year",
                                        figure=fig_pypi,
                                        config={"displayModeBar": False},
                                    ),
                                    html.Figcaption(
                                        "Number of new GA4GH-related PyPI packages first published each year.",
                                        style={"color": COLORS["grey"], "marginTop": "6px"},
                                    ),
                                ])
                            ),
                            className="shadow-sm h-100 w-100",
                            style={"borderRadius": "12px"},
                        ),
                        className="d-flex",
                        md=6,
                    ),
                ],
                className="mb-4",
            ),

            # Row 2: GA4GH standards by registered service count (full width)
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            html.Figure([
                                html.H5("GA4GH Standards by Registered Service Count",
                                        style={"marginBottom": "8px"}),
                                dcc.Graph(
                                    id="dev-standards-service-count",
                                    figure=fig_standards,
                                    config={"displayModeBar": False},
                                ),
                                html.Figcaption(
                                    "Number of services registered in the GA4GH Implementation Registry per standard.",
                                    style={"color": COLORS["grey"], "marginTop": "6px"},
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
        id="developer-charts",
        style={"display": "none"},
        className="epmc-section",
    )

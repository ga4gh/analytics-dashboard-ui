import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import dcc, html


# ---------------------------------------------------------------------------
# Figure builders
# ---------------------------------------------------------------------------

_STATUS_COLORS = {
    "Active":            "#2a9d8f",
    "Moderate activity": "#f4a261",
    "Inactive":          "#e76f51",
    "Archived":          "#adb5bd",
}

_STATUS_ORDER = ["Active", "Moderate activity", "Inactive", "Archived"]


def _workstream_activity_figure(gh_df: pd.DataFrame) -> go.Figure:
    if gh_df is None or gh_df.empty:
        return go.Figure().update_layout(title="No GitHub data available")

    if "workstream" not in gh_df.columns or "activity_status" not in gh_df.columns:
        return go.Figure().update_layout(title="Missing workstream or activity_status column")

    df = gh_df[["workstream", "activity_status"]].copy()
    df["workstream"] = df["workstream"].fillna("Unknown").astype(str).str.strip().replace("", "Unknown")
    df["activity_status"] = df["activity_status"].fillna("Unknown").astype(str)

    counts = (
        df.groupby(["workstream", "activity_status"])
        .size()
        .reset_index(name="count")
    )

    fig = px.bar(
        counts,
        x="count",
        y="workstream",
        color="activity_status",
        orientation="h",
        category_orders={"activity_status": _STATUS_ORDER},
        color_discrete_map=_STATUS_COLORS,
        labels={"count": "Repositories", "workstream": "Work Stream", "activity_status": "Status"},
        template="simple_white",
    )
    fig.update_traces(hovertemplate="%{y} — %{fullData.name}<br>Repos: %{x}<extra></extra>")
    fig.update_layout(
        height=440,
        margin={"l": 10, "r": 20, "t": 30, "b": 50},
        xaxis={"title": "Number of Repositories"},
        yaxis={"title": "", "automargin": True},
        legend={"title": "Activity Status", "orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        barmode="stack",
    )
    return fig


def _top_repos_interest_figure(gh_interest_df: pd.DataFrame) -> go.Figure:
    if gh_interest_df is None or gh_interest_df.empty:
        return go.Figure().update_layout(title="No GitHub interest data available")

    df = gh_interest_df.copy()
    if "name" not in df.columns or "total_interest" not in df.columns:
        return go.Figure().update_layout(title="Missing name or total_interest column")

    df = df.sort_values("total_interest", ascending=True)

    fig = px.bar(
        df,
        x="total_interest",
        y="name",
        orientation="h",
        labels={"total_interest": "Community Interest Score", "name": "Repository"},
        template="simple_white",
        color_discrete_sequence=["#1b75bb"],
        custom_data=["stargazers_count", "forks_count", "subscribers_count"],
    )
    fig.update_traces(
        hovertemplate=(
            "%{y}<br>"
            "Stars: %{customdata[0]}<br>"
            "Forks: %{customdata[1]}<br>"
            "Watchers: %{customdata[2]}<br>"
            "Total: %{x}<extra></extra>"
        )
    )
    fig.update_layout(
        height=400,
        margin={"l": 10, "r": 20, "t": 30, "b": 50},
        xaxis={"title": "Stars + Forks + Watchers"},
        yaxis={"title": "", "automargin": True},
    )
    return fig


# ---------------------------------------------------------------------------
# Public layout builder
# ---------------------------------------------------------------------------

def get_community_charts_section(
    gh_df: pd.DataFrame,
    gh_interest_df: pd.DataFrame,
):
    """
    GA4GH Community charts: GitHub workstream × activity status stacked bar
    and top 10 repos by community interest.
    Hidden by default; persona callback sets display:block.
    """
    fig_workstream = _workstream_activity_figure(gh_df)
    fig_interest   = _top_repos_interest_figure(gh_interest_df)

    return html.Div(
        [
            html.Div("GA4GH Community Overview", className="section-title"),

            # Row: workstream × activity + top repos side by side
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                html.Figure([
                                    html.H5("GitHub Repositories by Work Stream & Activity",
                                            style={"marginBottom": "8px"}),
                                    dcc.Graph(
                                        id="community-workstream-activity",
                                        figure=fig_workstream,
                                        config={"displayModeBar": False},
                                    ),
                                    html.Figcaption(
                                        "Activity status breakdown per GA4GH work stream — Active (pushed within 1 year), Moderate (1–3 years), Inactive (3+ years), Archived.",
                                        style={"fontSize": "13px", "color": "#777", "marginTop": "6px"},
                                    ),
                                ])
                            ),
                            className="mb-4 shadow-sm",
                            style={"borderRadius": "12px"},
                        ),
                        md=7,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                html.Figure([
                                    html.H5("Top 10 Repos by Community Interest",
                                            style={"marginBottom": "8px"}),
                                    dcc.Graph(
                                        id="community-top-repos-interest",
                                        figure=fig_interest,
                                        config={"displayModeBar": False},
                                    ),
                                    html.Figcaption(
                                        "Ranked by combined stars, forks, and watchers count.",
                                        style={"fontSize": "13px", "color": "#777", "marginTop": "6px"},
                                    ),
                                ])
                            ),
                            className="mb-4 shadow-sm",
                            style={"borderRadius": "12px"},
                        ),
                        md=5,
                    ),
                ],
            ),
        ],
        id="community-charts",
        style={"display": "none"},
        className="epmc-section",
    )

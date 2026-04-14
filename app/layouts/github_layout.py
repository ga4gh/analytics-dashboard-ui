import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from dash import html, dcc, dash_table
import pandas as pd
from app.utils.ga4gh_theme import apply_ga4gh_styling, COLORWAY

# ---------- FIGURES ----------
def fig_github_activity_bar(gh_activity_df, color_map=None):
    df = gh_activity_df.copy() if isinstance(gh_activity_df, pd.DataFrame) else pd.DataFrame(gh_activity_df)
    if df.empty:
        return apply_ga4gh_styling(go.Figure().update_layout(title="No activity data available"), height=700)

    for col in ("pushed_at", "last_updated"):
        if col in df.columns:
            df[col + "_str"] = pd.to_datetime(df[col], utc=True, errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            df[col + "_str"] = "N/A"

    df = df.sort_values("activity_score", ascending=False).reset_index(drop=True)
    ordered_names = df["name"].tolist()

    fig = go.Figure()
    workstreams = df["workstream"].fillna("none").astype(str)
    unique_ws = list(dict.fromkeys(workstreams.tolist()))

    for i, ws in enumerate(unique_ws):
        y_values = [
            row["activity_score"] if str(row.get("workstream", "none")) == ws else None
            for _, row in df.iterrows()
        ]
        color = color_map.get(ws) if color_map and ws in color_map else None

        fig.add_trace(go.Bar(
            x=ordered_names,
            y=y_values,
            name=ws,
            marker=dict(color=color) if color is not None else None,
            hovertemplate="Repo: %{x}<br>Activity Score: %{y:.4f}<extra></extra>",
        ))

    fig.update_layout(
        title={"text": "Most Recently Updated GA4GH-Related Repositories", "x": 0.0},
        barmode="overlay",
        xaxis=dict(categoryorder="array", categoryarray=ordered_names, tickangle=-45),
        margin=dict(l=40, r=20, t=80, b=150),
        height=700,
        xaxis_title="Repo Name",
        yaxis_title="Activity Score",
        legend_title_text="Workstream",
    )

    fig.update_traces(marker_line_width=0)
    return apply_ga4gh_styling(fig, height=700)


def fig_github_interest_metrics(gh_interest_df):
    df = gh_interest_df.copy() if isinstance(gh_interest_df, pd.DataFrame) else pd.DataFrame(gh_interest_df)
    if df.empty:
        return apply_ga4gh_styling(go.Figure().update_layout(title="No interest data available"), height=700)

    for col in ("subscribers_count", "stargazers_count", "forks_count"):
        if col not in df.columns:
            df[col] = 0
    df[["subscribers_count", "stargazers_count", "forks_count"]] = (
        df[["subscribers_count", "stargazers_count", "forks_count"]]
        .fillna(0)
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0)
    )

    df["total_interest"] = df["subscribers_count"] + df["stargazers_count"] + df["forks_count"]
    df = df.sort_values("total_interest", ascending=False)

    labels = {
        "name": "Repo Name",
        "value": "Metrics",
        "variable": "Metric",
        "subscribers_count": "Subscribers",
        "stargazers_count": "Stargazers",
        "forks_count": "Forks",
    }

    fig = px.bar(
        df,
        x="name",
        y=["subscribers_count", "stargazers_count", "forks_count"],
        title="Interest Metrics for GitHub Repositories",
        category_orders={"name": df["name"].tolist()},
        labels=labels,
    )

    rename_map = {"subscribers_count": "Subscribers", "stargazers_count": "Stargazers", "forks_count": "Forks"}
    for trace in fig.data:
        if trace.name in rename_map:
            trace.name = rename_map[trace.name]

    fig.update_layout(
        barmode="stack",
        xaxis_tickangle=-45,
        margin=dict(l=40, r=20, t=80, b=150),
        height=700,
        xaxis_title="Repo Name",
        yaxis_title="Total Interest",
        legend_title_text="Metric",
    )

    fig.update_traces(marker_line_width=0)
    return apply_ga4gh_styling(fig, height=700)


def fig_github_workstream_pie(gh_df):
    def _empty_fig():
        return apply_ga4gh_styling(go.Figure().update_layout(title="No workstream data available"), height=700)

    if gh_df is None:
        return _empty_fig()

    df = gh_df.copy() if isinstance(gh_df, pd.DataFrame) else pd.DataFrame(gh_df)
    if "workstream" not in df.columns:
        return _empty_fig()

    ws = df["workstream"].dropna().astype(str).str.strip()
    ws = ws[ws != ""]
    if ws.empty:
        return _empty_fig()

    counts = ws.value_counts().reset_index()
    counts.columns = ["workstream", "count"]
    labels = counts["workstream"].tolist()
    values = counts["count"].tolist()

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.3,
                textinfo="label+percent",
                hoverinfo="label+value+percent",
            )
        ]
    )

    fig.update_layout(title={"text": "Repository Workstreams", "x": 0.5}, height=700)
    return apply_ga4gh_styling(fig, height=700)


# ---------- LAYOUT ----------

def get_github_layout(gh_df, total_repositories):
    """
    Returns the GitHub page layout.
    """
    return dbc.Container(
        [
            


            # ---------- FILTERS ----------
            html.Div(
                [     
                    # Dummy filter (30%)
                    html.Div(
                        [
                            html.Label("Repository Type"),

                            dcc.Dropdown(
                                id="gh-repo-filter",
                                options=[
                                    {"label": "All", "value": "all"},
                                    {"label": "Active", "value": "active"},
                                    {"label": "Archived", "value": "archived"},
                                    {"label": "Experimental", "value": "experimental"},
                                ],
                                value="all",
                                clearable=False,
                            ),
                        ],
                        style={"width": "30%"},
                    ),  
                    html.Div(
                        [
                            html.Label("Top Repositories"),
                            dcc.Slider(
                                id="gh-top-n-slider",
                                min=5,
                                max=50,
                                step=5,
                                value=20,
                                marks={
                                    10: "10",
                                    20: "20",
                                    30: "30",
                                    40: "40",
                                    50: "50",
                                },
                                tooltip={"placement": "bottom", "always_visible": True},
                            )
                        ],
                        style={"width": "70%"},
                    ),
                ],
                style={
                    "display": "flex",
                    "gap": "20px",
                    "marginTop": "20px",
                    "marginBottom": "20px",
                },
            ),

            # ---------- GRAPHS  ----------
            # Row 1: activity bar + workstream pie (each half width)
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(dcc.Graph(id="gh-activity-bar-graph")),
                            className="mb-4 shadow-sm",
                            style={"borderRadius": "12px"},
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(dcc.Graph(id="gh-workstream-pie")),
                            className="mb-4 shadow-sm",
                            style={"borderRadius": "12px"},
                        ),
                        md=6,
                    ),
                ]
            ),

            # Row 2: interest metrics full-width
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(dcc.Graph(id="gh-interest-graph")),
                            className="mb-4 shadow-sm",
                            style={"borderRadius": "12px"},
                        ),
                        md=12,
                    ),
                ]
            ),




        ],
        fluid=True,
    )
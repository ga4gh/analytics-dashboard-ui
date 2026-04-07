import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from dash import html, dcc, dash_table
import pandas as pd

# ---------- FIGURES ----------
'''
def fig_github_activity_status_pie(gh_activity_counts):
    fig = go.Figure(
        data=[
            go.Pie(
                labels=gh_activity_counts["Category"],
                values=gh_activity_counts["Count"],
                hole=0.4,
                textinfo="label+percent",
                hoverinfo="label+value+percent",
            )
        ]
    )

    fig.update_layout(
        title={
            "text": "Activity Status of GitHub Repositories",
            "x": 0.5,
        },
        template="simple_white",
        height=550,
    )

    return fig
'''

def fig_github_activity_bar(gh_activity_df, color_map=None):
    # New signature: accept DataFrame or list-like and optional color_map produced
    # by the workstream pie so colors/legend match. Keep template/layout consistent
    # with other figures (simple_white) and match pie legend coloring.
    df = gh_activity_df.copy() if isinstance(gh_activity_df, pd.DataFrame) else pd.DataFrame(gh_activity_df)
    if df.empty:
        return go.Figure().update_layout(title="No activity data available")

    # Accept an explicit color_map mapping workstream -> color (preferred)

    # Ensure formatted date strings exist for hover display
    for col in ("pushed_at", "last_updated"):
        if col in df.columns:
            df[col + "_str"] = pd.to_datetime(df[col], utc=True, errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            df[col + "_str"] = "N/A"

    # Order repos by activity_score descending
    df = df.sort_values("activity_score", ascending=False).reset_index(drop=True)
    ordered_names = df["name"].tolist()

    # Build one trace per workstream but use ordered_names as x so ordering is preserved
    fig = go.Figure()
    workstreams = df["workstream"].fillna("none").astype(str)
    unique_ws = list(dict.fromkeys(workstreams.tolist()))

    for ws in unique_ws:
        y_values = [row["activity_score"] if (str(row.get("workstream", "none")) == ws) else None for _, row in df.iterrows()]
        color = None
        if color_map and ws in color_map:
            color = color_map[ws]

        fig.add_trace(
            go.Bar(
                x=ordered_names,
                y=y_values,
                name=ws,
                marker=dict(color=color) if color is not None else None,
                hovertemplate=(
                    "Repo: %{x}<br>"
                    "Activity Score: %{y:.4f}<br>"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        template="simple_white",
        title={"text": "Most Recently Updated GA4GH-Related Repositories", "x": 0.0},
        barmode="overlay",
        xaxis=dict(categoryorder="array", categoryarray=ordered_names, tickangle=-45),
        margin=dict(l=40, r=20, t=80, b=150),
        height=650,
        xaxis_title="Repo Name",
        yaxis_title="Activity Score",
        legend_title_text="Workstream",
    )

    fig.update_traces(marker_line_width=0)

    return fig


def fig_github_interest_metrics(gh_interest_df):
    # Accept DataFrame or list-like input and ensure ordering by total interest
    df = gh_interest_df.copy() if isinstance(gh_interest_df, pd.DataFrame) else pd.DataFrame(gh_interest_df)
    if df.empty:
        return go.Figure().update_layout(title="No interest data available")

    # Ensure numeric columns exist
    for col in ("subscribers_count", "stargazers_count", "forks_count"):
        if col not in df.columns:
            df[col] = 0
    df[["subscribers_count", "stargazers_count", "forks_count"]] = df[["subscribers_count", "stargazers_count", "forks_count"]].fillna(0).apply(pd.to_numeric, errors="coerce").fillna(0)

    # Compute a total interest metric and sort descending so largest appears first
    df = df.copy()
    df["total_interest"] = df["subscribers_count"] + df["stargazers_count"] + df["forks_count"]
    df = df.sort_values("total_interest", ascending=False)

    # Map raw column names to friendly legend labels
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
        template="simple_white",
        category_orders={"name": df["name"].tolist()},
        labels=labels,
    )

    # Axis and legend titles
    fig.update_layout(
        xaxis_title="Repo Name",
        yaxis_title="Total Interest",
        legend_title_text="Metric",
    )

    # Ensure legend entries use friendly names (strip trailing _count)
    rename_map = {
        "subscribers_count": "Subscribers",
        "stargazers_count": "Stargazers",
        "forks_count": "Forks",
    }
    for trace in fig.data:
        # trace.name may include the raw column name; map it when possible
        raw_name = getattr(trace, "name", None)
        if raw_name in rename_map:
            trace.name = rename_map[raw_name]

    fig.update_layout(
        barmode="stack",
        xaxis_tickangle=-45,
        margin=dict(l=40, r=20, t=80, b=150),
        height=650,
    )

    fig.update_traces(marker_line_width=0)

    return fig


def fig_github_workstream_pie(gh_df):
    """Pie chart of repository counts by `workstream` field (ignore null/empty).
    Accepts optional `color_map` and `labels_order` supplied by caller to ensure
    consistent color/label mapping between figures.
    """
    def _empty_fig():
        return go.Figure().update_layout(title="No workstream data available")

    if gh_df is None:
        return _empty_fig()

    # Accept either DataFrame or list-like
    df = gh_df.copy() if isinstance(gh_df, pd.DataFrame) else pd.DataFrame(gh_df)
    if "workstream" not in df.columns:
        return _empty_fig()

    # Filter out null/empty values
    ws = df["workstream"].dropna().astype(str).str.strip()
    ws = ws[ws != ""]
    if ws.empty:
        return _empty_fig()

    counts = ws.value_counts().reset_index()
    counts.columns = ["workstream", "count"]

    # Compute labels in descending count order
    labels = counts["workstream"].tolist()
    print(counts)
    print(labels)
    # Allow caller to request specific colors via DataFrame.attrs
    provided_color_map = None
    if hasattr(df, "attrs") and isinstance(df.attrs, dict):
        provided_color_map = df.attrs.get("color_map")

    # Build color list aligned to labels. Use provided_color_map when available,
    # otherwise use Plotly qualitative palette.
    palette = px.colors.qualitative.Plotly
    colors = []
    for i, lab in enumerate(labels):
        if provided_color_map and lab in provided_color_map:
            colors.append(provided_color_map[lab])
        else:
            colors.append(palette[i % len(palette)])

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=counts["count"],
                hole=0.3,
                textinfo="label+percent",
                hoverinfo="label+value+percent",
                marker=dict(colors=colors),
            )
        ]
    )

    fig.update_layout(
        title={"text": "Repository Work Streams", "x": 0.5},
        template="simple_white",
        height=550,
        legend=dict(traceorder="normal"),
    )

    return fig


# ---------- LAYOUT ----------

def get_github_layout(gh_df, total_repositories, workstreams):
    """
    Returns the GitHub page layout.
    """
    dropdown_options = [{"label": str(item), "value": item} for item in workstreams]
    return dbc.Container(
        [
            # ---------- FILTERS ----------
            html.Div(
                [     
                    # Dummy filter (30%)
                    html.Div(
                        [
                            html.Label("Work Stream"),

                            dcc.Dropdown(
                                id="gh-repo-filter",
                                options=dropdown_options,
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
                        style={"width": "50%"},
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
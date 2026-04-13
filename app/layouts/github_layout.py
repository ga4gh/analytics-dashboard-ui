import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from dash import html, dcc, dash_table
import pandas as pd

# ---------- FIGURES ----------
def fig_github_activity_status_pie(gh_activity_counts):
    df = gh_activity_counts.copy() if isinstance(gh_activity_counts, pd.DataFrame) else pd.DataFrame(gh_activity_counts)
    if df.empty or "Category" not in df.columns or "Count" not in df.columns:
        return go.Figure().update_layout(title="No activity status data available")

    category_order = [
        "High",
        "Moderate",
        "Low",
        "Archived",
    ]
    color_map = {
        "High": "#636EFA",
        "Moderate": "#EF553B",
        "Low": "#00CC96",
        "Archived": "#8E8E93",
    }

    df["Category"] = pd.Categorical(df["Category"], categories=category_order, ordered=True)
    df = df.sort_values("Category")

    fig = go.Figure(
        data=[
            go.Pie(
                labels=df["Category"],
                values=df["Count"],
                hole=0.4,
                textinfo="percent",
                hoverinfo="label+value+percent",
                marker={"colors": [color_map.get(c, "#A0A0A0") for c in df["Category"]]},
            )
        ]
    )

    fig.update_layout(
        title={
            "text": "Activity Status of the GA4GH GitHub Repositories",
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": {"size": 26, "color": "#2C3E50"},
        },
        plot_bgcolor="#f9f9f9",
        paper_bgcolor="#ffffff",
        legend_title_text="Activity Status",
        height=600,
    )

    return fig

def fig_github_activity_bar(gh_activity_df, color_map=None):
    df = gh_activity_df.copy() if isinstance(gh_activity_df, pd.DataFrame) else pd.DataFrame(gh_activity_df)
    if df.empty:
        return go.Figure().update_layout(title="No activity data available")

    # Format dates
    for col in ("pushed_at", "last_updated"):
        if col in df.columns:
            df[col + "_str"] = pd.to_datetime(df[col], utc=True, errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            df[col + "_str"] = "N/A"

    # Sort
    df = df.sort_values("activity_score", ascending=False).reset_index(drop=True)

    # Fill missing workstreams
    df["workstream"] = df["workstream"].fillna("none").astype(str)

    fig = go.Figure()

    for _, row in df.iterrows():
        ws = row["workstream"]
        color = color_map.get(ws) if color_map and ws in color_map else None

        fig.add_trace(
            go.Bar(
                x=[row["name"]],
                y=[row["activity_score"]],
                name=ws,
                marker=dict(color=color) if color else None,
                legendgroup=ws,
                showlegend=not any(t.name == ws for t in fig.data),  # show legend once per ws
                hovertemplate=(
                    f"Repo: {row['name']}<br>"
                    f"Activity Score: {row['activity_score']:.4f}<br>"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        template="simple_white",
        title={"text": "Most active GA4GH Repositories by Work Stream", "x": 0.0},
        barmode="group",
        xaxis=dict(tickangle=-45),
        margin=dict(l=40, r=20, t=80, b=150),
        height=650,
        xaxis_title="Repo Name",
        yaxis_title="Activity Score",
        legend_title_text="Work Stream",
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
    """Pie chart with short labels on slices, full name in legend & hover, consistent 1-decimal %."""
    def _empty_fig():
        return go.Figure().update_layout(title="No workstream data available")

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

    # Precompute percent to ensure 1 decimal
    counts["percent"] = counts["count"] / counts["count"].sum() * 100

    # Short form mapping
    short_map = {
        "Genomic Knowledge Standards": "GKS",
        "Cloud": "Cloud",
        "Tech/TASC": "TT",
        "Large Scale Genomics": "LSG",
        "Clinical and Phenotypic": "Clin-Pheno",
        "Discovery":"DD",
        "Regulatory and Ethics":"REWS",
        "Data Security":"DS",
        "Data Use and Researcher Identity":"DURI",
    }

    # Labels
    slice_labels = [short_map.get(lab, lab) for lab in counts["workstream"]]  # on slices
    legend_labels = counts["workstream"].tolist()  # full name in legend
    hover_labels = [f"{lab}: {pct:.1f}%" for lab, pct in zip(counts["workstream"], counts["percent"])]  # hover

    # Colors
    palette = px.colors.qualitative.Plotly
    provided_color_map = getattr(df, "attrs", {}).get("color_map", {})
    colors = [provided_color_map.get(lab, palette[i % len(palette)]) for i, lab in enumerate(counts["workstream"])]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=legend_labels,             # legend uses full names
                values=counts["count"],
                hole=0.3,
                text=[f"{lab}<br>{pct:.1f}%" for lab, pct in zip(slice_labels, counts["percent"])],  # short + percent
                textinfo="text",
                hovertext=hover_labels,           # hover shows full name + percent
                hoverinfo="text",
                marker=dict(colors=colors),
            )
        ]
    )

    fig.update_layout(
        title={"text": "GA4GH GitHub Repositories", "x": 0.5},
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
    dropdown_options = [{"label": "All", "value": "all"}] + [
        {"label": ws, "value": ws} for ws in workstreams
    ]
    
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
                                id="gh-workstream-filter",
                                options=dropdown_options,
                                value="all",
                                clearable=False,
                            ),
                        ],
                        style={"width": "25%"},
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
                        style={"width": "50%", "marginLeft": "auto"},
                    ),
                ],
                style={
                    "display": "flex",
                    "gap": "30px",
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
                            dbc.CardBody(
                                html.Figure([
                                    dcc.Graph(id="gh-activity-bar-graph"),
                                    html.Figcaption("Activity score of GA4GH repositories. Includes technical and foundational work streams, as well as TASC / Tech Team repositories. See methods section for definition of activity score.")
                                ])
                            ),
                            className="mb-4 shadow-sm",
                            style={"borderRadius": "12px"},
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                html.Figure([
                                    dcc.Graph(id="gh-activity-status-pie"),
                                    html.Figcaption("Relative proportion of GA4GH GitHub repositories at each activity status, which is determined from the number of days that have elapsed since the last update. High: last update less than 6 months ago; Moderate: last update 6 months to 2 years ago; Low: last update more than 2 years ago.")
                                ])
                            ),
                            className="mb-4 shadow-sm",
                            style={"borderRadius": "12px"},
                        ),
                        md=6,
                    ),
                ]
            ),

            # Row 2: workstream pie + interest metrics
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                html.Figure([
                                    dcc.Graph(id="gh-workstream-pie"),
                                    html.Figcaption("Relative proportion of GA4GH GitHub repositories by work stream. Includes technical and foundational work streams, as well as TASC / Tech Team repositories.")
                                ])
                            ),
                            className="mb-4 shadow-sm",
                            style={"borderRadius": "12px"},
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                html.Figure([
                                    dcc.Graph(id="gh-interest-graph"),
                                    html.Figcaption("Total number of subscribers, stargazers, and forks for each GA4GH GitHub repository.")
                                ])
                            ),
                            className="mb-4 shadow-sm",
                            style={"borderRadius": "12px"},
                        ),
                        md=6,
                    ),
                ]
            ),
        ],
        fluid=True,
    )
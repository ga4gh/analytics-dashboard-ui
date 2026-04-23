from dash import Input, Output
from app.services.github_client import prepare_github_data
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from dash import html
import pandas as pd
import numpy as np


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
            "font": {"color": "#2C3E50"},
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

    for col in ("pushed_at", "last_updated"):
        if col in df.columns:
            df[col + "_str"] = pd.to_datetime(df[col], utc=True, errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            df[col + "_str"] = "N/A"

    df = df.sort_values("activity_score", ascending=False).reset_index(drop=True)
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
                showlegend=not any(t.name == ws for t in fig.data),
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
    df = gh_interest_df.copy() if isinstance(gh_interest_df, pd.DataFrame) else pd.DataFrame(gh_interest_df)
    if df.empty:
        return go.Figure().update_layout(title="No interest data available")

    for col in ("subscribers_count", "stargazers_count", "forks_count"):
        if col not in df.columns:
            df[col] = 0
    df[["subscribers_count", "stargazers_count", "forks_count"]] = df[["subscribers_count", "stargazers_count", "forks_count"]].fillna(0).apply(pd.to_numeric, errors="coerce").fillna(0)

    df = df.copy()
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
        template="simple_white",
        category_orders={"name": df["name"].tolist()},
        labels=labels,
    )

    fig.update_layout(
        xaxis_title="Repo Name",
        yaxis_title="Total Interest",
        legend_title_text="Metric",
    )

    rename_map = {
        "subscribers_count": "Subscribers",
        "stargazers_count": "Stargazers",
        "forks_count": "Forks",
    }
    for trace in fig.data:
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
    counts["percent"] = counts["count"] / counts["count"].sum() * 100

    short_map = {
        "Genomic Knowledge Standards": "GKS",
        "Cloud": "Cloud",
        "Tech/TASC": "TT",
        "Large Scale Genomics": "LSG",
        "Clinical and Phenotypic": "Clin-Pheno",
        "Discovery": "DD",
        "Regulatory and Ethics": "REWS",
        "Data Security": "DS",
        "Data Use and Researcher Identity": "DURI",
    }

    slice_labels = [short_map.get(lab, lab) for lab in counts["workstream"]]
    legend_labels = counts["workstream"].tolist()
    hover_labels = [f"{lab}: {pct:.1f}%" for lab, pct in zip(counts["workstream"], counts["percent"])]

    palette = px.colors.qualitative.Plotly
    provided_color_map = getattr(df, "attrs", {}).get("color_map", {})
    colors = [provided_color_map.get(lab, palette[i % len(palette)]) for i, lab in enumerate(counts["workstream"])]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=legend_labels,
                values=counts["count"],
                hole=0.3,
                text=[f"{lab}<br>{pct:.1f}%" for lab, pct in zip(slice_labels, counts["percent"])],
                textinfo="text",
                hovertext=hover_labels,
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

def register_github_callbacks(app):
    gh_df, gh_activity_df, gh_activity_counts, gh_interest_df, total_repositories, workstreams = prepare_github_data()
    if "workstream" not in gh_df.columns:
        gh_df["workstream"] = "N/A"
    else:
        gh_df["workstream"] = gh_df["workstream"].fillna("N/A").astype(str)

    search_columns = ["name", "description"]
    display_columns = [
        "name",
        "workstream",
        "owner",
        "repo_link",
        "description",
        "stargazers_count",
        "forks_count",
        "is_archived",
        "watchers_count",
        "subscribers_count",
        "open_issues_count",
        "last_updated",
        "pushed_at",
    ]
    
    @app.callback(
        Output("repo-details", "children"),
        Input("github-projects-table", "selected_rows")
    )
    def show_repo_details(selected_rows):
        if not selected_rows:
            return dbc.Alert("Select a repository to see details", color="info")
        
        repo = gh_df.iloc[selected_rows[0]]
        
        return dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.H4(repo["name"], className="mb-0 me-3"),
                    dbc.Badge(
                        f"⭐ Stars: {repo['stargazers_count']}",
                        color="primary",
                        className="me-2 fs-6 p-2",
                        pill=True,
                    ),
                    dbc.Badge(
                        f"🍴 Forks: {repo['forks_count']}",
                        color="secondary",
                        className="me-2 fs-6 p-2",
                        pill=True,
                    ),
                    dbc.Badge(
                        f"👀 Watchers: {repo['watchers_count']}",
                        color="dark",
                        className="fs-6 p-2",
                        pill=True,
                    ),
                ], style={"display": "flex", "alignItems": "center", "flexWrap": "wrap", "gap": "8px"})
            ),

            dbc.CardBody([

                html.P(repo["description"], className="mb-3"),
                html.Hr(),
                html.P(f"Open Issues: {repo['open_issues_count']}"),
                html.P(f"Subscribers: {repo['subscribers_count']}"),
                html.P(f"Last Updated: {repo['last_updated'].strftime('%Y-%m-%d %H:%M')}"),
                html.P(f"Pushed At: {repo['pushed_at'].strftime('%Y-%m-%d %H:%M')}"),
                #html.P(f"Archived: {repo['is_archived']}"),
                html.Br(),
                dbc.Button(
                    "Open Repository",
                    href=repo["repo_link"],
                    target="_blank",
                )

            ])

        ], style={"boxShadow": "0 4px 10px rgba(0,0,0,0.1)"})

    @app.callback(
        Output("github-projects-table", "data"),
        Input("github-table-search", "value")
    )
    def update_table(search_value):
        if not search_value:
            return gh_df[display_columns].to_dict("records")

        mask = gh_df[search_columns].apply(
            lambda col: col.astype(str).str.contains(search_value, case=False, na=False)
        ).any(axis=1)

        filtered_df = gh_df[mask]

        return filtered_df[display_columns].to_dict("records")
    
    @app.callback(
    Output("gh-activity-bar-graph", "figure"),
    Output("gh-activity-status-pie", "figure"),
    Output("gh-workstream-pie", "figure"),
    Output("gh-interest-graph", "figure"),
    Input("gh-top-n-slider", "value"),
    Input("gh-workstream-filter", "value"),  # Only the dropdown now
    )
    def update_github_graphs(top_n, workstream_filter):
        df_filtered = gh_df.copy()

        # Apply workstream filter (if not "all")
        if workstream_filter != "all":
            df_filtered = df_filtered[df_filtered["workstream"] == workstream_filter]

        # Top N applies only to bar chart
        df_top = df_filtered.sort_values("activity_score", ascending=False).head(top_n)

        # Activity status donut (requested thresholds)
        status_conditions = [
            (df_filtered["is_archived"] == False) & (df_filtered["days_since_pushed_at"] < 180),
            (df_filtered["is_archived"] == False)
            & (df_filtered["days_since_pushed_at"] >= 180)
            & (df_filtered["days_since_pushed_at"] <= 730),
            (df_filtered["is_archived"] == False) & (df_filtered["days_since_pushed_at"] > 730),
            (df_filtered["is_archived"] == True),
        ]
        status_choices = [
            "High",
            "Moderate",
            "Low",
            "Archived",
        ]
        status_series = np.select(status_conditions, status_choices, default="Unknown")
        gh_activity_counts = (
            pd.Series(status_series)
            .value_counts()
            .rename_axis("Category")
            .reset_index(name="Count")
        )

        # Workstream color map (deterministic)
        ws_series = df_filtered["workstream"].dropna().astype(str).str.strip() if "workstream" in df_filtered.columns else pd.Series([], dtype=str)
        ws_series = ws_series[ws_series != ""]
        labels = ws_series.value_counts().index.tolist()

        palette = px.colors.qualitative.Plotly
        color_map = {lab: palette[i % len(palette)] for i, lab in enumerate(labels)}

        # Store color_map in DataFrame.attrs
        df_top.attrs["color_map"] = color_map
        df_filtered.attrs["color_map"] = color_map

        # Build figures
        fig_status = fig_github_activity_status_pie(gh_activity_counts)
        fig_ws = fig_github_workstream_pie(df_filtered)
        fig3 = fig_github_interest_metrics(df_filtered)
        fig2 = fig_github_activity_bar(df_top, color_map=color_map)

        return fig2, fig_status, fig_ws, fig3
from dash import Input, Output
from app import app
from app.services.github_client import prepare_github_data
from app.layouts.github_layout import (
    fig_github_activity_bar,
    fig_github_interest_metrics,
    fig_github_workstream_pie,
)
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from dash import html, dcc, dash_table
import pandas as pd

def register_github_callbacks(app):
    gh_df, gh_activity_df, gh_activity_counts, gh_interest_df, total_repositories = prepare_github_data()
    search_columns = ["name", "description"]
    display_columns = [
        "name",
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
                html.H4(repo["name"])
            ),

            dbc.CardBody([

                html.P(repo["description"], className="mb-3"),

                dbc.Row([
                    dbc.Col(dbc.Badge(f"⭐ Stars: {repo['stargazers_count']}", color="primary", className="me-2")),
                    dbc.Col(dbc.Badge(f"🍴 Forks: {repo['forks_count']}", color="secondary", className="me-2")),
                    dbc.Col(dbc.Badge(f"👀 Watchers: {repo['watchers_count']}", color="dark", className="me-2")),
                ], className="mb-3"),

                html.Hr(),

                html.P(f"Open Issues: {repo['open_issues_count']}"),
                html.P(f"Subscribers: {repo['subscribers_count']}"),
                html.P(f"Last Updated: {repo['last_updated']}"),
                html.P(f"Pushed At: {repo['pushed_at']}"),
                html.P(f"Archived: {repo['is_archived']}"),

                html.Br(),

                dbc.Button(
                    "Open Repository",
                    href=repo["repo_link"],
                    target="_blank",
                    color="primary"
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
        Output("gh-workstream-pie", "figure"),
        Output("gh-interest-graph", "figure"),
        Input("gh-top-n-slider", "value"),
        Input("gh-repo-filter", "value"),
    )
    def update_github_graphs(top_n, repo_filter):

        df = gh_df.copy()
        # Start with a copy and apply repo filter; the Top-N selection
        # should only affect the activity bar chart, not the pie or interest metrics.
        df_filtered = gh_df.copy()

        if repo_filter == "active":
            df_filtered = df_filtered[df_filtered["is_archived"] == False]

        elif repo_filter == "archived":
            df_filtered = df_filtered[df_filtered["is_archived"] == True]

        # Top N applies only to bar chart
        df_top = df_filtered.sort_values("activity_score", ascending=False).head(top_n)

        # PIE CHART should be computed from the filtered full set (not top_n)
        gh_activity_counts = (
            df_filtered.assign(
                Category=df_filtered["is_archived"].map({True: "Archived", False: "Active"})
            )
            .groupby("Category")
            .size()
            .reset_index(name="Count")
        )

        # Compute deterministic workstream color_map (labels ordered by descending count)
        ws_series = df_filtered["workstream"].dropna().astype(str).str.strip() if "workstream" in df_filtered.columns else pd.Series([], dtype=str)
        ws_series = ws_series[ws_series != ""]
        labels = ws_series.value_counts().index.tolist()

        palette = px.colors.qualitative.Plotly
        color_map = {lab: palette[i % len(palette)] for i, lab in enumerate(labels)}

        # build color map deterministically from filtered df and store in attrs
        # store on DataFrame.attrs so pandas won't warn
        if not hasattr(df_top, "attrs"):
            df_top.attrs = {}
        df_top.attrs["color_map"] = color_map
        if not hasattr(df_filtered, "attrs"):
            df_filtered.attrs = {}
        df_filtered.attrs["color_map"] = color_map

        # Build figures using the shared color_map so legends/colors match 1:1
        fig_ws = fig_github_workstream_pie(df_filtered)
        fig3 = fig_github_interest_metrics(df_filtered)
        fig2 = fig_github_activity_bar(df_top, color_map=color_map)

        return fig2, fig_ws, fig3
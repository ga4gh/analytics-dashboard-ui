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

def fig_github_activity_bar(gh_activity_df):
    # Accept list-like or DataFrame and prepare formatted date strings for hover
    df = gh_activity_df.copy() if isinstance(gh_activity_df, pd.DataFrame) else pd.DataFrame(gh_activity_df)
    if df.empty:
        return go.Figure().update_layout(title="No activity data available")

    # Ensure pushed_at / last_updated string columns exist for hover display
    for col in ("pushed_at", "last_updated"):
        if col in df.columns:
            df[col + "_str"] = pd.to_datetime(df[col], utc=True, errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            df[col + "_str"] = "N/A"

    # Build the bar chart with customdata including the formatted date strings
    fig = px.bar(
        df,
        x="name",
        y="activity_score",
        title="Most Recently Updated GA4GH-Related Repositories",
        custom_data=["days_since_pushed_at", "days_since_last_updated", "pushed_at_str", "last_updated_str"],
        template="simple_white",
    )

    hovertemplate = (
        "Repo: %{x}<br>"
        "Activity Score: %{y:.4f}<br>"
        "Days since last commit: %{customdata[0]}<br>"
        "Days since last repo update: %{customdata[1]}<br>"
        "Last Pushed: %{customdata[2]}<br>"
        "Last Updated: %{customdata[3]}<extra></extra>"
    )

    fig.update_traces(hovertemplate=hovertemplate)

    fig.update_layout(
        xaxis_tickangle=-45,
        margin=dict(l=40, r=20, t=80, b=150),
        height=650,
    )

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
        yaxis_title="Metrics",
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
    """Pie chart of repository counts by `workstream` field (ignore null/empty)."""
    if gh_df is None or gh_df.empty:
        return go.Figure().update_layout(title="No workstream data available")

    # Accept either DataFrame or list-like
    df = gh_df.copy() if isinstance(gh_df, pd.DataFrame) else pd.DataFrame(gh_df)
    if "workstream" not in df.columns:
        return go.Figure().update_layout(title="No workstream data available")

    # Filter out null/empty values
    ws = df["workstream"].dropna().astype(str).str.strip()
    ws = ws[ws != ""]
    if ws.empty:
        return go.Figure().update_layout(title="No workstream data available")

    counts = ws.value_counts().reset_index()
    counts.columns = ["workstream", "count"]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=counts["workstream"],
                values=counts["count"],
                hole=0.3,
                textinfo="label+percent",
                hoverinfo="label+value+percent",
            )
        ]
    )
    fig.update_layout(title={"text": "Repository Workstreams", "x": 0.5}, template="simple_white", height=550)
    return fig


# ---------- LAYOUT ----------

def get_github_layout(gh_df, total_repositories):
    """
    Returns the GitHub page layout.
    """
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
    return dbc.Container(
        [

            html.H1(
                "GitHub Analytics Dashboard",
                style={
                    "textAlign": "center",
                    "marginTop": "20px",
                    "marginBottom": "10px",
                    "fontSize": "60px",
                    "fontWeight": "bold",
                    "color": "#2C3E50",
                    "textShadow": "2px 2px #BDC3C7"
                }
            ),

            html.H2(
                f"Total GitHub Repositories: {total_repositories}",
                style={'textAlign': 'center', 'margin-bottom': '20px', 'color': "#9DAAB8"}
            ),
            
                # Table + details will be rendered after the graphs 

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
                            html.Label("Top N Repositories"),
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


            # Search box for DataTable
            dcc.Input(
                id='github-table-search',
                type='text',
                placeholder='Search repositories...',
                debounce=False,
                style={
                    'margin-bottom': '15px',
                    'width': '350px',
                    'padding': '8px',
                    'border-radius': '5px',
                    'border': '1px solid #ccc'
                }
            ),

            # ---------- TABLE + DETAILS  ----------
            dbc.Row([

            # LEFT: TABLE
            dbc.Col([

                dash_table.DataTable(
                    id="github-projects-table",
                    columns=[
                        {"name": "Project", "id": "name"},
                        #{"name": "Description", "id": "description"},
                        {"name": "Archived", "id": "is_archived"},
                    ],
                    data=gh_df[display_columns].to_dict("records"),
                    row_selectable="single",
                    page_size=10,
                    style_table={"overflowX": "auto"},
                    style_cell={
                        "textAlign": "left",
                        "padding": "10px",
                        "whiteSpace": "normal",
                    },
                    style_header={
                        "backgroundColor": "#2c3e50",
                        "color": "white",
                        "fontWeight": "bold"
                    }
                )

            ], width=6),

            # RIGHT: DETAILS PANEL
            dbc.Col([
                html.Div(id="repo-details")
            ], width=6)

        ]),

        ],
        fluid=True,
    )
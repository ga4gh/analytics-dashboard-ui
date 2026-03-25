import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from dash import html, dcc, dash_table
import pandas as pd

# ---------- FIGURES ----------
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


def fig_github_activity_bar(gh_activity_df):
    fig = px.bar(
        gh_activity_df,
        x="name",
        y="activity_score",
        title="Most Recently Updated GA4GH-Related Repositories",
        custom_data=["days_since_pushed_at", "days_since_last_updated"],
        template="simple_white",
    )

    fig.update_traces(
        hovertemplate=(
            "Repo: %{x}<br>"
            "Activity Score: %{y:.4f}<br>"
            "Days since last commit: %{customdata[0]}<br>"
            "Days since last repo update: %{customdata[1]}<extra></extra>"
        )
    )

    fig.update_layout(
        xaxis_tickangle=-45,
        margin=dict(l=40, r=20, t=80, b=150),
        height=650,
    )

    return fig


def fig_github_interest_metrics(gh_interest_df):
    fig = px.bar(
        gh_interest_df,
        x="name",
        y=["subscribers_count", "stargazers_count", "forks_count"],
        title="Interest Metrics for GitHub Repositories",
        template="simple_white",
    )

    fig.update_layout(
        barmode="stack",
        xaxis_tickangle=-45,
        margin=dict(l=40, r=20, t=80, b=150),
        height=650,
    )

    fig.update_traces(marker_line_width=0)

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
                                max=120,
                                step=20,
                                value=20,
                                marks={
                                    20: "20",
                                    40: "40",
                                    60: "60",
                                    80: "80",
                                    100: "100",
                                    120: "All"
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
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(dcc.Graph(id="gh-activity-status-graph")),
                            className="mb-4 shadow-sm",
                            style={"borderRadius": "12px"},
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(dcc.Graph(id="gh-activity-bar-graph")),
                            className="mb-4 shadow-sm",
                            style={"borderRadius": "12px"},
                        ),
                        md=6,
                    ),
                ]
            ),

            # If odd number of graphs, render the remaining one full-width on its own row
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(dcc.Graph(id="gh-interest-graph")),
                            className="mb-4 shadow-sm",
                            style={"borderRadius": "12px"},
                        ),
                        md=12,
                    )
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
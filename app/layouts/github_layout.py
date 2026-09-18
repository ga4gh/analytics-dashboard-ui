import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table

from app.utils.ga4gh_theme import chart_toolbar, chart_info_icon
from app.constants.constants import STYLE_HEIGHT_4X


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
                                className="list-filter",
                            ),
                        ],
                        className="chart-filter-quarter",
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
                        className="chart-slider-wrap chart-slider-wrap--push-right",
                    ),
                ],
                className="chart-filter-row chart-filter-row--github",
            ),

            # ---------- GRAPHS  ----------
            # Row 1: activity bar + workstream pie (each half width)
            # mb-4 lives on the Row, not the Cards — a card's own margin-bottom
            # is invisible once h-100 stretches it to fill the flexed column
            # (there's no room left below it to show the margin).
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                html.Figure([
                                    chart_toolbar("gh-activity-bar-graph"),
                                    html.Div([html.Span("Most active GA4GH Repositories by Work Stream")] + chart_info_icon("gh-activity-bar-graph", "Bar chart of GA4GH repositories ranked by activity score. Activity score is computed from commit frequency, open issues, and recency of updates. Filterable by work stream."), className="chart-heading"),
                                    dcc.Graph(
                                        id="gh-activity-bar-graph",
                                        style={"height": STYLE_HEIGHT_4X},
                                        config={"responsive": True, "displayModeBar": False}
                                    ),
                                    html.Figcaption("Activity score of GA4GH repositories. Includes technical and foundational work streams, as well as TASC / Tech Team repositories. See methods section for definition of activity score.")
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
                                    chart_toolbar("gh-activity-status-pie"),
                                    html.Div([html.Span("Activity Status of the GA4GH GitHub Repositories")] + chart_info_icon("gh-activity-status-pie", "Proportion of repositories by activity status: High (updated < 6 months ago), Moderate (6 months–2 years), Low (> 2 years), or Archived."), className="chart-heading"),
                                    dcc.Graph(
                                        id="gh-activity-status-pie",
                                        className="chart-aspect-tall",
                                        style={"height": STYLE_HEIGHT_4X},
                                        config={"responsive": True, "displayModeBar": False},
                                    ),
                                    html.Figcaption("Relative proportion of GA4GH GitHub repositories at each activity status, which is determined from the number of days that have elapsed since the last update. High: last update less than 6 months ago; Moderate: last update 6 months to 2 years ago; Low: last update more than 2 years ago.")
                                ])
                            ),
                            className="shadow-sm h-100 w-100",
                            style={"borderRadius": "12px"},
                        ),
                        className="d-flex",
                        md=6,
                    ),
                ],
                className="mb-4 chart-cards-row",
            ),

            # Row 2: workstream pie + interest metrics
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                html.Figure([
                                    chart_toolbar("gh-workstream-pie"),
                                    html.Div([html.Span("GA4GH GitHub Repositories")] + chart_info_icon("gh-workstream-pie", "Donut chart showing how GA4GH GitHub repositories are distributed across work streams such as Cloud, GKS, Data Security, and others."), className="chart-heading"),
                                    dcc.Graph(
                                        id="gh-workstream-pie",
                                        className="chart-aspect-tall",
                                        style={"height": STYLE_HEIGHT_4X},
                                        config={"responsive": True, "displayModeBar": False},
                                    ),
                                    html.Figcaption("Relative proportion of GA4GH GitHub repositories by work stream. Includes technical and foundational work streams, as well as TASC / Tech Team repositories.")
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
                                    chart_toolbar("gh-interest-graph"),
                                    html.Div([html.Span("Interest Metrics for GitHub Repositories")] + chart_info_icon("gh-interest-graph", "Stacked bar chart of community interest signals — stars, forks, and subscribers — for each GA4GH repository. Higher values indicate broader adoption and community engagement."), className="chart-heading"),
                                    dcc.Graph(
                                        id="gh-interest-graph",
                                        style={"height": STYLE_HEIGHT_4X},
                                        config={"responsive": True, "displayModeBar": False}
                                    ),
                                    html.Figcaption("Total number of subscribers, stargazers, and forks for each GA4GH GitHub repository.")
                                ])
                            ),
                            className="shadow-sm h-100 w-100",
                            style={"borderRadius": "12px"},
                        ),
                        className="d-flex",
                        md=6,
                    ),
                ],
                className="chart-cards-row",
            ),
        ],
        fluid=True,
    )
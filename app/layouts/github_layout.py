import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table

from app.utils.ga4gh_theme import chart_expand_button


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
            # mb-4 lives on the Row, not the Cards — a card's own margin-bottom
            # is invisible once h-100 stretches it to fill the flexed column
            # (there's no room left below it to show the margin).
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                html.Figure([
                                    chart_expand_button("gh-activity-bar-graph"),
                                    html.H5("Most active GA4GH Repositories by Work Stream", style={"marginBottom": "8px"}),
                                    dcc.Graph(id="gh-activity-bar-graph"),
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
                                    chart_expand_button("gh-activity-status-pie"),
                                    html.H5("Activity Status of the GA4GH GitHub Repositories", style={"marginBottom": "8px"}),
                                    dcc.Graph(id="gh-activity-status-pie", style={"minHeight": "900px", "flex": "1 1 auto"}),
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
                className="mb-4",
            ),

            # Row 2: workstream pie + interest metrics
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                html.Figure([
                                    chart_expand_button("gh-workstream-pie"),
                                    html.H5("GA4GH GitHub Repositories", style={"marginBottom": "8px"}),
                                    dcc.Graph(id="gh-workstream-pie", style={"minHeight": "900px", "flex": "1 1 auto"}),
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
                                    chart_expand_button("gh-interest-graph"),
                                    html.H5("Interest Metrics for GitHub Repositories", style={"marginBottom": "8px"}),
                                    dcc.Graph(id="gh-interest-graph"),
                                    html.Figcaption("Total number of subscribers, stargazers, and forks for each GA4GH GitHub repository.")
                                ])
                            ),
                            className="shadow-sm h-100 w-100",
                            style={"borderRadius": "12px"},
                        ),
                        className="d-flex",
                        md=6,
                    ),
                ]
            ),
        ],
        fluid=True,
    )
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd

def get_pypi_layout(pypi_details, total_packages):
    """
    Returns the PyPI page layout.
    """
    if isinstance(pypi_details, list):
        pypi_details = pd.DataFrame(pypi_details)
    if pypi_details is None or pypi_details.empty:
        pypi_details = pd.DataFrame(columns=[
            "project_name", "description", "author_name",
            "author_email", "category", "versions_count"
        ])

    # Get unique values for filters
    author_options = [{"label": x, "value": x} for x in sorted(pypi_details["author_name"].dropna().unique())]
    email_options = [{"label": x, "value": x} for x in sorted(pypi_details["author_email"].dropna().unique())]
    category_options = [{"label": x, "value": x} for x in sorted(pypi_details["category"].dropna().unique())]
    
    display_columns_pypi = ["project_name", "category"]
    
    return dbc.Container(
        [
            


            html.Div(
            [
                # Row 1
                html.Div(
                    [
                        html.Div([
                            html.Label("Author"),
                            dcc.Dropdown(
                                id="filter-author",
                                options=author_options,
                                multi=True,
                                placeholder="Select authors"
                            )
                        ], style={"width": "48%"}),

                        html.Div([
                            html.Label("Email"),
                            dcc.Dropdown(
                                id="filter-email",
                                options=email_options,
                                multi=True,
                                placeholder="Select emails"
                            )
                        ], style={"width": "48%"})
                    ],
                    style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "margin-bottom": "15px"
                    }
                ),

                # Row 2
                html.Div(
                    [
                        html.Div([
                            html.Label("Category"),
                            dcc.Dropdown(
                                id="filter-category",
                                options=category_options,
                                multi=True,
                                placeholder="Select categories"
                            )
                        ], style={"width": "48%"}),

                        html.Div([
                            html.Label("Top Packages"),
                            dcc.Slider(
                                id="top-n-slider",
                                min=5,
                                max=50,
                                step=5,
                                value=10,
                                marks={i: str(i) for i in range(5, 55, 5)},
                                tooltip={"placement": "bottom", "always_visible": True}
                            )
                        ], style={"width": "48%"})
                    ],
                    style={
                        "display": "flex",
                        "justifyContent": "space-between"
                    }
                ),
            ],
            style={
                "margin-top": "20px",
                "margin-bottom": "20px"
            }
        ),
            # ---------- GRAPHS  ----------
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                html.Figure([
                                    dcc.Graph(id="datatable-bar"),
                                    html.Figcaption("Total number of versions for the top GA4GH-related PyPI packages, sorted in descending order by number of versions.")
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
                                    dcc.Graph(id="category-distribution"),
                                    html.Figcaption("Relative proportion of package category for GA4GH-related PyPI packages.")
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
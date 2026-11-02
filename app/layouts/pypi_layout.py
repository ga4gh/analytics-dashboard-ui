from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd

from app.utils.ga4gh_theme import chart_toolbar, chart_info_icon
from app.constants.constants import STYLE_HEIGHT_3X

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
                                placeholder="Select authors",
                                className="list-filter",
                            )
                        ], className="chart-filter-half"),

                        html.Div([
                            html.Label("Email"),
                            dcc.Dropdown(
                                id="filter-email",
                                options=email_options,
                                multi=True,
                                placeholder="Select emails",
                                className="list-filter",
                            )
                        ], className="chart-filter-half")
                    ],
                    className="chart-filter-row",
                    style={
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
                                placeholder="Select categories",
                                className="list-filter",
                            )
                        ], className="chart-filter-half"),

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
                        ], className="chart-slider-wrap chart-filter-half")
                    ],
                    className="chart-filter-row chart-filter-row--pypi",
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
                                    chart_toolbar("datatable-bar"),
                                    html.Div([html.Span(id="datatable-bar-title")] + chart_info_icon("datatable-bar", "Bar chart of the top GA4GH-related PyPI packages by total number of published versions. Use the slider to adjust how many packages are shown, and the filters to narrow by author or category."), className="chart-heading"),
                                    dcc.Graph(
                                        id="datatable-bar",
                                        style={"height": STYLE_HEIGHT_3X},
                                        config={"responsive": True, "displayModeBar": False}
                                    ),
                                    html.Figcaption("Total number of versions for the top GA4GH-related PyPI packages, sorted in descending order by number of versions.")
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
                                    chart_toolbar("category-distribution"),
                                    html.Div([html.Span("Category Distribution")] + chart_info_icon("category-distribution", "Donut chart of GA4GH-related PyPI packages grouped by category: GA4GH Standard (implements a GA4GH spec), Implementation (standalone tool), or GA4GH Mentions (references GA4GH in metadata)."), className="chart-heading"),
                                    dcc.Graph(
                                        id="category-distribution",
                                        className="chart-aspect-tall",
                                        style={"height": STYLE_HEIGHT_3X},
                                        config={"responsive": True, "displayModeBar": False},
                                    ),
                                    html.Figcaption("Relative proportion of package category for GA4GH-related PyPI packages.")
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


            
        ],
        fluid=True,
    )
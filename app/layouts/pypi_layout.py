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
            
            # Table + details will be rendered after the graphs 

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
                            html.Label("Top N Packages"),
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
                            dbc.CardBody(dcc.Graph(id='datatable-bar')),
                            className="mb-4 shadow-sm",
                            style={"borderRadius": "12px"},
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(dcc.Graph(id='category-distribution')),
                            className="mb-4 shadow-sm",
                            style={"borderRadius": "12px"},
                        ),
                        md=6,
                    ),
                ]
            ),

            # Search box for DataTable
            dcc.Input(
                id='table-search',
                type='text',
                placeholder='Search projects...',
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
                dbc.Row([
                    dbc.Col(
                        dash_table.DataTable(
                            id="projects-table",
                            columns=[
                                {"name": "Project", "id": "project_name"},
                                {"name": "Category", "id": "category"},
                            ],
                            data=pypi_details[["project_name", "category"]].to_dict("records"),
                            row_selectable="single",
                            page_size=10,
                            sort_action="native",
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
                        ),
                        width=6
                    ),

                    dbc.Col(
                        html.Div(id="pypi-project-details"),
                        width=6
                    )
                ])

            ]),
            
        ],
        fluid=True,
    )
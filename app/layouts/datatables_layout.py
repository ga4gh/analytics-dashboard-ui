from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd


def get_datatables_layout(
    epmc_entries_df,
    gh_df,
    pypi_details,
):
    """
    Returns the combined bottom data tables section with search bars.
    
    Args:
        epmc_entries_df: DataFrame for EPMC entries
        gh_df: DataFrame for GitHub repositories
        pypi_details: DataFrame for PyPI packages
    
    Returns:
        dbc.Container with three DataTables (EPMC, GitHub, PyPI)
    """
    
    # Ensure DataFrames are valid
    if epmc_entries_df is None or epmc_entries_df.empty:
        epmc_entries_df = pd.DataFrame(columns=["title", "pub_year"])
    if gh_df is None or gh_df.empty:
        gh_df = pd.DataFrame(columns=["name", "is_archived"])
    if pypi_details is None or pypi_details.empty:
        pypi_details = pd.DataFrame(columns=["project_name", "category"])
    
    return dbc.Container(
        [
            # ========== EPMC TABLE SECTION ==========
            html.H4("Europe PMC Publications", style={"marginTop": "40px", "marginBottom": "15px"}),
            
            dcc.Input(
                id="epmc-table-search",
                type="text",
                placeholder="Search Publications...",
                debounce=False,
                style={
                    "margin-bottom": "15px",
                    "width": "350px",
                    "padding": "8px",
                    "border-radius": "5px",
                    "border": "1px solid #ccc",
                },
            ),

            dbc.Row(
                [
                    # LEFT: EPMC Table
                    dbc.Col(
                        [
                            dash_table.DataTable(
                                id="epmc-entries-table",
                                columns=[
                                    {"name": "Title", "id": "title"},
                                    {"name": "Year", "id": "pub_year"},
                                ],
                                data=epmc_entries_df.to_dict("records") if not epmc_entries_df.empty else [],
                                row_selectable="single",
                                selected_rows=[0],
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
                                    "fontWeight": "bold",
                                },
                            )
                        ],
                        md=6,
                    ),
                    # RIGHT: EPMC Details
                    dbc.Col(html.Div(id="epmc-entry-details"), md=6),
                ],
            ),

            html.Hr(style={"marginTop": "40px", "marginBottom": "40px"}),

            # ========== GITHUB TABLE SECTION ==========
            html.H4("GitHub Repositories", style={"marginBottom": "15px"}),
            
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

            dbc.Row([
                # LEFT: GITHUB TABLE
                dbc.Col([
                    dash_table.DataTable(
                        id="github-projects-table",
                        columns=[
                            {"name": "Project", "id": "name"},
                            {"name": "Archived", "id": "is_archived"},
                        ],
                        data=gh_df[["name", "is_archived"]].to_dict("records") if not gh_df.empty and "name" in gh_df.columns else [],
                        row_selectable="single",
                        selected_rows=[0],
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
                ], md=6),

                # RIGHT: GITHUB DETAILS PANEL
                dbc.Col([
                    html.Div(id="repo-details")
                ], md=6)

            ]),

            html.Hr(style={"marginTop": "40px", "marginBottom": "40px"}),

            # ========== PYPI TABLE SECTION ==========
            html.H4("PyPI Packages", style={"marginBottom": "15px"}),
            
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

            dbc.Row([
                dbc.Col(
                    dash_table.DataTable(
                        id="projects-table",
                        columns=[
                            {"name": "Project", "id": "project_name"},
                            {"name": "Category", "id": "category"},
                        ],
                        data=pypi_details[["project_name", "category"]].to_dict("records") if not pypi_details.empty and "project_name" in pypi_details.columns else [],
                        row_selectable="single",
                        selected_rows=[0],
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
                    md=6
                ),

                dbc.Col(
                    html.Div(id="pypi-project-details"),
                    md=6
                )
            ]),

        ],
        fluid=True,
    )

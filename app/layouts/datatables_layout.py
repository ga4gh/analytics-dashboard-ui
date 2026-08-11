from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd


DATATABLE_FONT_FAMILY = "'Proxima Nova', 'ProximaNova', 'Helvetica Neue', Arial, sans-serif"


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
        gh_df = pd.DataFrame(columns=["name", "workstream"])
    if pypi_details is None or pypi_details.empty:
        pypi_details = pd.DataFrame(columns=["project_name", "category"])

    # Build dropdown options from EPMC data
    epmc_year_options = []
    epmc_affiliation_options = []

    if not epmc_entries_df.empty:
        if "pub_year" in epmc_entries_df.columns:
            years = pd.to_numeric(epmc_entries_df["pub_year"], errors="coerce").dropna().astype(int).unique()
            epmc_year_options = [
                {"label": str(y), "value": str(y)}
                for y in sorted(years, reverse=True)
            ]

        if "affiliation" in epmc_entries_df.columns:
            affiliations = set()
            for aff_text in epmc_entries_df["affiliation"].dropna():
                aff_text = str(aff_text).strip()
                if not aff_text:
                    continue
                # Split on semicolons — the affiliation field is a concatenated string
                # of institutions separated by "; "
                for part in aff_text.split(";"):
                    part = part.strip()
                    if part:
                        affiliations.add(part)
            epmc_affiliation_options = [
                {"label": html.Span(a, title=a, className="epmc-affiliation-option"), "value": a, "search": a}
                for a in sorted(affiliations)
            ]
    
    return dbc.Container(
        [
            # ========== EPMC TABLE SECTION ==========
            html.H4("Europe PMC Publications", style={"marginTop": "40px", "marginBottom": "15px"}),
            html.Figcaption("Metadata for all GA4GH-related articles found in Europe PMC.", style={"marginTop": "15px", "marginBottom": "15px"}),
            html.Div(
                [
                    dcc.Input(
                        id="epmc-table-search",
                        type="text",
                        placeholder="Search by Title...",
                        debounce=False,
                        style={
                            "width": "350px",
                            "padding": "8px",
                            "border-radius": "5px",
                            "border": "1px solid #ccc",
                        },
                    ),
                    dcc.Dropdown(
                        id="epmc-year-filter",
                        options=epmc_year_options,
                        placeholder="Filter by Year",
                        clearable=True,
                        className="custom-dropdown",
                        style={"width": "160px", "height": "38px"},
                    ),
                    dcc.Input(
                        id="epmc-affiliation-filter",
                        type="text",
                        placeholder="Search by Affiliation...",
                        debounce=True,
                        style={
                            "width": "350px",
                            "padding": "8px",
                            "border-radius": "5px",
                            "border": "1px solid #ccc",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "gap": "12px",
                    "alignItems": "center",
                    "marginBottom": "15px",
                },
            ),
            
            dcc.Store(id="first-author-store"),
            dcc.Store(id="first-affiliation-store"),
            dbc.Row(
                [
                    # LEFT: EPMC Table
                    dbc.Col(
                        [
                            html.Div(
                                dash_table.DataTable(
                                    id="epmc-entries-table",
                                    columns=[
                                        {"name": "Title", "id": "title"},
                                        {"name": "Year", "id": "pub_year"},
                                    ],
                                    data=epmc_entries_df.to_dict("records") if not epmc_entries_df.empty else [],
                                    export_format="csv",
                                    row_selectable="single",
                                    selected_rows=[0],
                                    page_size=15,
                                    sort_action="native",
                                    style_table={"overflowX": "auto"},
                                    style_cell={
                                        "textAlign": "left",
                                        "padding": "10px",
                                        "whiteSpace": "normal",
                                        "fontFamily": DATATABLE_FONT_FAMILY,
                                    },
                                    style_header={
                                        "backgroundColor": "#2c3e50",
                                        "color": "white",
                                        "fontWeight": "bold",
                                        "fontFamily": DATATABLE_FONT_FAMILY,
                                    },
                                ),
                                className="datatable-controls-inline",
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
            html.Figcaption("Metadata and usage metrics for all GA4GH-related GitHub repositories.", style={"marginTop": "15px", "marginBottom": "15px"}),
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
                    html.Div(
                        dash_table.DataTable(
                            id="github-projects-table",
                            columns=[
                                {"name": "Project", "id": "name"},
                                {"name": "Work Stream", "id": "workstream"},
                            ],
                            data = gh_df.to_dict("records") if not gh_df.empty and all(col in gh_df.columns for col in ["name", "workstream"]) else [],
                            row_selectable="single",
                            export_format="csv",
                            selected_rows=[0],
                            page_size=15,
                            style_table={"overflowX": "auto"}, 
                            style_cell={ "textAlign": "left", "padding": "10px", "whiteSpace": "normal", "fontFamily": DATATABLE_FONT_FAMILY }, 
                            style_header={ "backgroundColor": "#2c3e50", "color": "white", "fontWeight": "bold", "fontFamily": DATATABLE_FONT_FAMILY }
                        ),
                        className="datatable-controls-inline",
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
            html.Figcaption("Project metadata for all GA4GH-related PyPI packages.", style={"marginTop": "15px", "marginBottom": "15px"}),
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
                    html.Div(
                        dash_table.DataTable(
                            id="projects-table",
                            columns=[
                                {"name": "Project", "id": "project_name"},
                                {"name": "Category", "id": "category"},
                            ],
                            data=pypi_details[["project_name", "category"]].to_dict("records") if not pypi_details.empty and "project_name" in pypi_details.columns else [],
                            export_format="csv",
                            row_selectable="single",
                            selected_rows=[0],
                            page_size=15,
                            sort_action="native",
                            style_table={"overflowX": "auto"},
                            style_cell={
                                "textAlign": "left",
                                "padding": "10px",
                                "whiteSpace": "normal",
                                "fontFamily": DATATABLE_FONT_FAMILY,
                            },
                            style_header={
                                "backgroundColor": "#2c3e50",
                                "color": "white",
                                "fontWeight": "bold",
                                "fontFamily": DATATABLE_FONT_FAMILY,
                            }
                        ),
                        className="datatable-controls-inline",
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

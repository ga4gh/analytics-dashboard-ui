from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc

# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

def get_epmc_layout(entries_df, countries_df, authors_df, total_entries, citations):
    """
    Build and return the full EPMC page layout using cached data.
    """
    return dbc.Container(
        [


            # ---------- FILTERS ----------
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Top Authors"),
                            dcc.Slider(
                                id="epmc-top-n-slider",
                                min=5,
                                max=50,
                                step=5,
                                value=15,
                                marks={i: str(i) for i in range(5, 55, 5)},
                                tooltip={
                                    "placement": "bottom",
                                    "always_visible": True,
                                },
                            ),
                        ],
                        style={"width": "50%"},
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
                            dbc.CardBody(
                                html.Figure([
                                    dcc.Graph(id="epmc-authors-bar"),
                                    html.Figcaption("Bar chart of the number of GA4GH-related articles authored by the top individuals.")
                                ]),
                                id="epmc-authors-card-body",
                            ),
                            className="mb-4 shadow-sm",
                            style={"borderRadius": "12px"},
                        ),
                        md=12,
                    ),
                ]
            ),
            # Countries pie + Most-cited publications side-by-side
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                html.Figure([
                                    dcc.Graph(id="epmc-countries-pie"),
                                    html.Figcaption("Relative proportion of country affiliations for all authors of GA4GH-related articles. Country affiliation is determined from each author’s affiliation for all publications.")
                                ])
                            ),
                            className="mb-4 shadow-sm h-100 w-100",
                            style={"borderRadius": "12px"},
                        ),
                        className="d-flex",
                        md=6,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                html.Div(
                                    [
                                        html.H5("Most Cited GA4GH Publications", style={"marginBottom": "12px"}),
                                        html.Figcaption("Table of the most cited GA4GH-related articles, sorted in descending order by number of citations.", style={"marginBottom": "12px"}),
                                        html.Div(
                                            dash_table.DataTable(
                                                id="epmc-most-cited-table",
                                                columns=[
                                                    {"name": "Article", "id": "article_link", "presentation": "markdown"},
                                                    {"name": "Title", "id": "title"},
                                                    {"name": "Citations", "id": "cited_by_count"},
                                                ],
                                                data=[],
                                                page_size=20,
                                                style_table={"height": "100%", "overflowX": "auto", "overflowY": "auto"},
                                                style_cell={
                                                    "textAlign": "left",
                                                    "padding": "4px 6px",
                                                    "fontSize": "13px",
                                                    "lineHeight": "1.15",
                                                    "fontFamily": "'Proxima Nova', 'ProximaNova', 'Helvetica Neue', Arial, sans-serif",
                                                    "whiteSpace": "normal",
                                                },
                                                style_header={
                                                    "backgroundColor": "#2c3e50",
                                                    "color": "white",
                                                    "fontWeight": "bold",
                                                    "padding": "5px 6px",
                                                    "fontFamily": "'Proxima Nova', 'ProximaNova', 'Helvetica Neue', Arial, sans-serif",
                                                },
                                                style_data_conditional=[
                                                    {"if": {"column_id": "article_link"}, "width": "8%", "textAlign": "center"},
                                                    {"if": {"column_id": "title"}, "width": "76%"},
                                                    {"if": {"column_id": "cited_by_count"}, "width": "16%", "textAlign": "right"},
                                                ],
                                                css=[
                                                    {"selector": ".dash-cell-value p", "rule": "margin: 0; line-height: 1.1;"},
                                                    {"selector": "td[data-dash-column='article_link'] a", "rule": "display:inline-block; padding:2px 8px; border:1px solid #0d6efd; background-color:#0d6efd; color:#fff; border-radius:0.375rem; text-decoration:none; font-size:12px; font-weight:500; line-height:1.1;"},
                                                ],
                                                markdown_options={"link_target": "_blank"},
                                            ),
                                            style={"flex": "1 1 auto", "minHeight": 0},
                                        ),
                                    ],
                                    style={"display": "flex", "flexDirection": "column", "height": "100%"}
                                )
                            , style={"height": "100%"}),
                            className="mb-4 shadow-sm h-100 w-100 epmc-most-cited-card",
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

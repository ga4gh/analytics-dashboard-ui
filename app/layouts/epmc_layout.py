from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc

from app.utils.ga4gh_theme import COLORS, chart_expand_button
from app.layouts.funder_layout import _annual_publications_figure

# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

def get_epmc_layout(entries_df, countries_df, authors_df, total_entries, citations):
    """
    Build and return the full EPMC page layout using cached data.
    """
    return dbc.Container(
        [
            dcc.Store(id="epmc-countries-hidden-store", data=[]),

            # ---------- FILTERS ----------
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Top Authors"),
                            dcc.Slider(
                                id="epmc-top-n-slider",
                                min=5,
                                max=50,
                                step=5,
                                value=15,
                                marks={i: str(i) for i in range(5, 55, 5)},
                                tooltip={"placement": "bottom", "always_visible": True},
                            ),
                        ],
                        md=6,
                    ),
                    dbc.Col(
                        [
                            html.Label("Top Countries"),
                            dcc.Slider(
                                id="epmc-top-countries-slider",
                                min=5,
                                max=25,
                                step=5,
                                value=15,
                                marks={i: str(i) for i in range(5, 30, 5)},
                                tooltip={"placement": "bottom", "always_visible": True},
                            ),
                        ],
                        md=6,
                    ),
                ],
                className="mb-4",
            ),

            # ---------- GRAPHS  ----------
            # Authors bar + Countries pie side-by-side
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div(id="epmc-authors-bar-title", className="chart-heading"),
                                    html.Div(style={"flex": "1"}),
                                    html.Figure([
                                        chart_expand_button("epmc-authors-bar"),
                                        dcc.Graph(
                                            id="epmc-authors-bar",
                                            style={"height": "280px"},
                                        ),
                                        html.Figcaption("Bar chart of the number of GA4GH-related articles authored by the top individuals.")
                                    ]),
                                ],
                                id="epmc-authors-card-body",
                                style={"display": "flex", "flexDirection": "column"},
                            ),
                            className="mb-4 shadow-sm h-100",
                            style={"borderRadius": "12px"},
                        ),
                        md=6,
                        className="d-flex flex-column",
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                html.Figure([
                                    chart_expand_button("epmc-countries-pie"),
                                    html.Div("Affiliation - Countries Represented", className="chart-heading"),
                                    dcc.Graph(
                                        id="epmc-countries-pie",
                                        style={"height": "280px"},
                                        config={"responsive": True},
                                    ),
                                    html.Div(id="epmc-countries-legend", className="country-legend",
                                             style={"marginTop": "1rem"}),
                                    html.Figcaption("Relative proportion of country affiliations for all authors of GA4GH-related articles. Country affiliation is determined from each author's affiliation for all publications.")
                                ])
                            ),
                            className="mb-4 shadow-sm h-100",
                            style={"borderRadius": "12px"},
                        ),
                        md=6,
                        className="d-flex flex-column",
                    ),
                ],
                className="align-items-stretch",
            ),
            # Annual publications + Most cited table side-by-side
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                html.Figure([
                                    chart_expand_button("epmc-publications-trend"),
                                    html.Div("Annual GA4GH Publications", className="chart-heading"),
                                    dcc.Graph(
                                        id="epmc-publications-trend",
                                        figure=_annual_publications_figure(entries_df),
                                        config={"displayModeBar": False},
                                        style={"height": "280px"},
                                    ),
                                    html.Figcaption("Number of GA4GH-related articles published per year from Europe PMC."),
                                ])
                            ),
                            className="mb-4 shadow-sm h-100",
                            style={"borderRadius": "12px"},
                        ),
                        md=6,
                        className="d-flex flex-column",
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                html.Div([
                                    html.Div("Most Cited GA4GH Publications", className="chart-heading"),
                                html.Figcaption("Table of the most cited GA4GH-related articles, sorted in descending order by number of citations.", style={"marginBottom": "12px"}),
                                dash_table.DataTable(
                                    id="epmc-most-cited-table",
                                    columns=[
                                        {"name": "Article", "id": "article_link", "presentation": "markdown"},
                                        {"name": "Title", "id": "title"},
                                        {"name": "Citations", "id": "cited_by_count"},
                                    ],
                                    data=[],
                                    page_size=10,
                                    style_table={"overflowX": "auto"},
                                    style_data={
                                        "height": "auto",
                                        "whiteSpace": "normal",
                                        "lineHeight": "1",
                                    },
                                    style_cell={
                                        "textAlign": "left", "padding": "4px 6px",
                                        "fontSize": "13px",
                                        "fontFamily": "'Figtree-Regular', 'Figtree', sans-serif",
                                        "verticalAlign": "top",
                                    },
                                    style_header={
                                        "backgroundColor": COLORS["dark"], "color": "white",
                                        "fontWeight": "bold", "padding": "5px 6px",
                                        "fontFamily": "'Figtree-SemiBold', 'Figtree', sans-serif",
                                    },
                                    style_cell_conditional=[
                                        {"if": {"column_id": "article_link"}, "width": "8%", "textAlign": "center"},
                                        {"if": {"column_id": "title"}, "width": "76%", "textAlign": "left"},
                                        {"if": {"column_id": "cited_by_count"}, "width": "16%", "textAlign": "right"},
                                    ],
                                    css=[
                                        {"selector": ".dash-cell-value p", "rule": "margin: 0; line-height: 1.1;"},
                                        {"selector": "td[data-dash-column='article_link'] a", "rule": f"display:inline-block; padding:2px 8px; border:1px solid {COLORS['orange']}; background-color:{COLORS['orange']}; color:{COLORS['white']}; border-radius:0; text-decoration:none; font-size:12px; font-weight:500; line-height:1.1; transition: background-color 0.2s ease, border-color 0.2s ease;"},
                                        {"selector": "td[data-dash-column='article_link'] a:hover", "rule": f"border-color:{COLORS['red']}; background-color:{COLORS['red']};"},
                                        {"selector": "td[data-dash-column='article_link'] a::after", "rule": "font-family:'FontAwesomeSolid'; font-style:normal; font-weight:normal; content:'\\f08e'; margin-left:0.4em;"},
                                    ],
                                    markdown_options={"link_target": "_blank"},
                                ),
                            ])
                        ),
                        className="mb-4 shadow-sm h-100 epmc-most-cited-card",
                        style={"borderRadius": "12px"},
                    ),
                    md=6,
                    className="d-flex flex-column",
                ),
                ],
                className="align-items-stretch",
            ),


        ],
        fluid=True,
    )

# app/pages/home.py

from dash import html
import dash_bootstrap_components as dbc
from dash import register_page

from app.services.overview_client import (
    pm_df,
    gh_df,
    pypi_df,
)

register_page(
    __name__,
    path="/",
    title="GA4GH Analytics Dashboard",
    description="Welcome to the GA4GH Analytics Dashboard",
)


def indicator_card(value, label, color, small=False):
    
    return dbc.Card(
        dbc.CardBody(
            [
                html.H3(
                    value,
                    style={
                        "margin": "0",
                        "fontSize": "26px",
                        "fontWeight": "600",
                        "color": "#2C3E50",
                    },
                ),
                html.Div(label, style={"fontSize": "14px", "color": "#77787B"}),
            ],
            style={"padding": "12px 16px"},
        ),
        style={
            "borderRadius": "10px",
            "border": "1px solid #E6E6E6",
            "borderRight": f"12px solid {color}",
            "height": "72px",
        },
        className="shadow-sm",
    )


layout = dbc.Container(
    [

        # ---------- TITLE ----------
        html.H1(
            "GA4GH Analytics Dashboard",
            style={
                "fontSize": "56px",
                "fontWeight": "700",
                "color": "#2C3E50",
                "marginBottom": "25px",
                "marginTop": "30px",
            },
        ),

        # ---------- DESCRIPTION + LOGO ----------
        dbc.Row(
            [

                dbc.Col(
                    [
                        html.P(
                            "Analytics are important for standards organisations like GA4GH "
                            "as it helps to make data-driven decisions. The GA4GH Tech Team "
                            "is building an analytics dashboard to enable our community to "
                            "quantify the impact of standards, policy frameworks and products "
                            "that have been actively developed over the last 12 years.",
                            style={
                                "fontSize": "18px",
                                "color": "#6C757D",
                                "lineHeight": "1.6",
                            },
                        ),

                        html.P(
                            "Collaborators across Work Streams can use this dashboard to "
                            "understand how their contributions advance genomic data sharing, "
                            "gather intelligence to guide future product development, and "
                            "identify implementation opportunities.",
                            style={
                                "fontSize": "18px",
                                "color": "#6C757D",
                                "lineHeight": "1.6",
                            },
                        ),
                    ],
                    md=8,
                ),

                dbc.Col(
                    html.Img(
                        src="/assets/logo-full-color.svg",
                        style={
                            "width": "100%",
                            "maxHeight": "220px",
                            "objectFit": "contain",
                        },
                    ),
                    md=4,
                    style={"textAlign": "center"},
                ),

            ],
            align="center",
        ),

        html.Br(),

        # ---------- INFO BADGES ----------
        dbc.Row(
            [
                dbc.Col(
                    dbc.Badge(
                        "Data Updated: 2026-03-13",
                        color="light",
                        text_color="dark",
                        className="p-2",
                    ),
                    width="auto",
                ),

                dbc.Col(
                    dbc.Badge(
                        "Created by: GA4GH Technical Team",
                        color="light",
                        text_color="dark",
                        className="p-2",
                    ),
                    width="auto",
                ),

                dbc.Col(
                    dbc.Badge(
                        "Data Source: GitHub, PyPI, EuropePMC",
                        color="light",
                        text_color="dark",
                        className="p-2",
                    ),
                    width="auto",
                ),
            ],
            className="mb-4",
            align="center",
        ),

        # ---------- KPI INDICATORS ----------
            dbc.Row(
                [
                    dbc.Col(
                        indicator_card(
                            f"{len(pm_df):,}",
                            "PubMed Records",
                            "#1B75BB",
                        ),
                        md=2,
                    ),

                    dbc.Col(
                        indicator_card(
                            f"{len(gh_df):,}",
                            "GitHub Repositories",
                            "#4FAEDC",
                        ),
                        md=2,
                    ),

                    dbc.Col(
                        indicator_card(
                            f"{len(pypi_df):,}",
                            "PyPI Packages",
                            "#FAA633",
                        ),
                        md=2,
                    ),
                    
                    dbc.Col(
                        indicator_card(
                            f"{len(pm_df):,}",
                            "PubMed Records",
                            "#1B75BB",
                        ),
                        md=2,
                    ),

                    dbc.Col(
                        indicator_card(
                            f"{len(gh_df):,}",
                            "GitHub Repositories",
                            "#4FAEDC",
                        ),
                        md=2,
                    ),

                    dbc.Col(
                        indicator_card(
                            f"{len(pypi_df):,}",
                            "PyPI Packages",
                            "#FAA633",
                        ),
                        md=2,
                    ),
                ],
                className="mb-4",
            ),
    

        # ---------- MODULE CARDS ----------
        dbc.Row(
            [

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H3("PyPI Analytics"),
                                html.P("View package trends, categories, and versions"),
                                dbc.Button("Open", id="open-pypi", color="primary", size="lg"),
                            ]
                        ),
                        className="shadow-sm",
                        style={"textAlign": "center", "height": "250px"},
                    ),
                    md=4,
                ),

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H3("GitHub Analytics"),
                                html.P("Repository activity and metrics"),
                                dbc.Button("Open", id="open-github", color="success", size="lg"),
                            ]
                        ),
                        className="shadow-sm",
                        style={"textAlign": "center", "height": "250px"},
                    ),
                    md=4,
                ),

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H3("PubMed"),
                                html.P("View publication trends and metrics"),
                                dbc.Button("Open", id="open-pubmed", color="warning", size="lg"),
                            ]
                        ),
                        className="shadow-sm",
                        style={"textAlign": "center", "height": "250px"},
                    ),
                    md=4,
                ),

            ],
            justify="center",
        ),

        html.Br(),

        html.Div(id="module-content", style={"marginTop": "40px"}),

        # ---------- FOOTER ----------
        html.Div(
            "© 2026 GA4GH Analytics Dashboard",
            style={
                "textAlign": "center",
                "marginTop": "50px",
                "marginBottom": "50px",
                "color": "#95A5A6",
            },
        ),

    ],
    fluid=True,
)
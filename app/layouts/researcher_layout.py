import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import dcc, html

# Reuse the shared annual publications figure
from app.layouts.funder_layout import _annual_publications_figure
from app.utils.ga4gh_theme import COLORS, PUBLICATIONS_COLORWAY, chart_expand_button


# ---------------------------------------------------------------------------
# Figure builders
# ---------------------------------------------------------------------------

_PUB_TYPE_COLORS = {
    "Journal Article":  PUBLICATIONS_COLORWAY[0],
    "Review":           PUBLICATIONS_COLORWAY[1],
    "Preprint":         PUBLICATIONS_COLORWAY[2],
    "Comment / Letter": PUBLICATIONS_COLORWAY[3],
    "Other":            COLORS["grey"],
}


def _pub_type_figure(pub_types: list) -> go.Figure:
    if not pub_types:
        return go.Figure().update_layout(title="No publication type data available")

    df = pd.DataFrame(pub_types)

    fig = px.pie(
        df,
        names="type",
        values="count",
        color="type",
        color_discrete_map=_PUB_TYPE_COLORS,
        template="simple_white",
        hole=1/3,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        textfont_color="white",
        hovertemplate="%{label}<br>Articles: %{value}<br>Share: %{percent}<extra></extra>",
    )
    fig.update_layout(
        # autosize (not a fixed height) — paired with config={"responsive":
        # True} on the dcc.Graph and .chart-aspect-tall in style.css so this
        # scales with the card's actual width at any viewport.
        autosize=True,
        margin={"l": 20, "r": 20, "t": 30, "b": 20},
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5),
        hoverlabel=dict(font_color="white"),
    )
    return fig


def _open_access_figure(entries_df) -> go.Figure:
    if entries_df is None or entries_df.empty or "is_open_access" not in entries_df.columns:
        return go.Figure().update_layout(title="No open access data available")

    counts = entries_df["is_open_access"].value_counts().reset_index()
    counts.columns = ["status", "count"]
    counts["label"] = counts["status"].map({True: "Open Access", False: "Restricted"})

    fig = px.pie(
        counts,
        names="label",
        values="count",
        color="label",
        color_discrete_map={"Open Access": COLORS["darkgreen"], "Restricted": COLORS["grey"]},
        template="simple_white",
        hole=1/3,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        textfont_color="white",
        hovertemplate="%{label}<br>Articles: %{value}<br>Share: %{percent}<extra></extra>",
    )
    fig.update_layout(
        # autosize (not a fixed height) — paired with config={"responsive":
        # True} on the dcc.Graph and .chart-aspect-tall in style.css so this
        # scales with the card's actual width at any viewport.
        autosize=True,
        margin={"l": 20, "r": 20, "t": 30, "b": 20},
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5),
        hoverlabel=dict(font_color="white"),
    )
    return fig


# ---------------------------------------------------------------------------
# Public layout builder
# ---------------------------------------------------------------------------

def get_researcher_charts_section(entries_df, pub_types_list):
    """
    Researcher-specific charts: publication types bar + open access donut.
    Hidden by default; persona callback sets display:block.
    """
    pub_type_fig = _pub_type_figure(pub_types_list)
    oa_fig = _open_access_figure(entries_df)

    return html.Div(
        [
            html.Div("Research Profile", className="section-title"),

            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                html.Figure([
                                    chart_expand_button("researcher-pub-type-donut"),
                                    html.H5("Publication Types", style={"marginBottom": "1rem"}),
                                    dcc.Graph(
                                        id="researcher-pub-type-donut",
                                        figure=pub_type_fig,
                                        className="chart-aspect-tall",
                                        config={"responsive": True},
                                    ),
                                    html.Figcaption(
                                        "Each article is assigned one primary type — counts sum to the total unique article count.",
                                        style={"color": COLORS["grey"], "marginTop": "6px"},
                                    ),
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
                                    chart_expand_button("researcher-oa-donut"),
                                    html.H5("Open Access Status", style={"marginBottom": "1rem"}),
                                    dcc.Graph(
                                        id="researcher-oa-donut",
                                        figure=oa_fig,
                                        className="chart-aspect-tall",
                                        config={"responsive": True},
                                    ),
                                    html.Figcaption(
                                        "Proportion of GA4GH-related publications available as open access.",
                                        style={"color": COLORS["grey"], "marginTop": "6px"},
                                    ),
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
        id="researcher-charts",
        style={"display": "none"},
        className="epmc-section",
    )

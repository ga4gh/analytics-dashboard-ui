import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import dcc, html

# Reuse the shared annual publications figure
from app.layouts.funder_layout import _annual_publications_figure


# ---------------------------------------------------------------------------
# Figure builders
# ---------------------------------------------------------------------------

_PUB_TYPE_COLORS = {
    "Journal Article": "#1b75bb",
    "Review":          "#e76f51",
    "Preprint":        "#2a9d8f",
    "Comment / Letter": "#f4a261",
    "Other":           "#adb5bd",
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
        hole=0.4,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="%{label}<br>Articles: %{value}<br>Share: %{percent}<extra></extra>",
    )
    fig.update_layout(
        height=380,
        margin={"l": 20, "r": 20, "t": 30, "b": 20},
        showlegend=True,
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
        color_discrete_map={"Open Access": "#2a9d8f", "Restricted": "#adb5bd"},
        template="simple_white",
        hole=0.4,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="%{label}<br>Articles: %{value}<br>Share: %{percent}<extra></extra>",
    )
    fig.update_layout(
        height=380,
        margin={"l": 20, "r": 20, "t": 30, "b": 20},
        showlegend=True,
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
                                    html.H5("Publication Types", style={"marginBottom": "8px"}),
                                    dcc.Graph(
                                        id="researcher-pub-type-donut",
                                        figure=pub_type_fig,
                                        config={"displayModeBar": False},
                                    ),
                                    html.Figcaption(
                                        "Each article is assigned one primary type — counts sum to the total unique article count.",
                                        style={"fontSize": "13px", "color": "#777", "marginTop": "6px"},
                                    ),
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
                                    html.H5("Open Access Status", style={"marginBottom": "8px"}),
                                    dcc.Graph(
                                        id="researcher-oa-donut",
                                        figure=oa_fig,
                                        config={"displayModeBar": False},
                                    ),
                                    html.Figcaption(
                                        "Proportion of GA4GH-related publications available as open access.",
                                        style={"fontSize": "13px", "color": "#777", "marginTop": "6px"},
                                    ),
                                ])
                            ),
                            className="mb-4 shadow-sm",
                            style={"borderRadius": "12px"},
                        ),
                        md=6,
                    ),
                ],
            ),
        ],
        id="researcher-charts",
        style={"display": "none"},
        className="epmc-section",
    )

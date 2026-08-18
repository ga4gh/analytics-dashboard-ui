import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import dcc, html


# ---------------------------------------------------------------------------
# Figure builders
# ---------------------------------------------------------------------------

def _annual_publications_figure(entries_df):
    if entries_df is None or entries_df.empty or "pub_year" not in entries_df.columns:
        return go.Figure().update_layout(title="No publication year data available")

    yearly = (
        entries_df[entries_df["pub_year"].notna()]
        .groupby("pub_year")
        .size()
        .reset_index(name="count")
        .sort_values("pub_year")
    )
    yearly["pub_year"] = yearly["pub_year"].astype(int)

    fig = px.bar(
        yearly,
        x="pub_year",
        y="count",
        labels={"pub_year": "Year", "count": "Publications"},
        template="simple_white",
        color_discrete_sequence=["#1b75bb"],
    )
    fig.update_traces(hovertemplate="Year: %{x}<br>Publications: %{y}<extra></extra>")
    fig.update_layout(
        height=380,
        margin={"l": 40, "r": 20, "t": 30, "b": 50},
        xaxis={"tickmode": "linear", "dtick": 1, "title": "Year"},
        yaxis={"title": "Number of Publications"},
        bargap=0.25,
    )
    return fig


def _top_agencies_figure(agencies: list) -> go.Figure:
    if not agencies:
        return go.Figure().update_layout(title="No funding agency data available")

    df = pd.DataFrame(agencies[:15]).sort_values("count", ascending=True)
    fig = px.bar(
        df,
        x="count",
        y="agency",
        orientation="h",
        labels={"count": "Number of Grants", "agency": "Funding Agency"},
        template="simple_white",
        color_discrete_sequence=["#1b75bb"],
    )
    fig.update_traces(hovertemplate="%{y}<br>Grants: %{x}<extra></extra>")
    fig.update_layout(
        height=480,
        margin={"l": 10, "r": 20, "t": 30, "b": 50},
        xaxis={"title": "Number of Grants"},
        yaxis={"title": "", "automargin": True},
    )
    return fig


_REGION_MAP = {
    "US": [
        "NHGRI NIH HHS", "NCI NIH HHS", "National Institutes of Health",
        "NIH HHS", "NHLBI NIH HHS", "NIA NIH HHS", "NIAID NIH HHS",
        "NIMH NIH HHS", "NIDDK NIH HHS", "NINDS NIH HHS",
        "National Human Genome Research Institute", "National Cancer Institute",
        "National Science Foundation", "Department of Defense",
    ],
    "UK": [
        "Wellcome Trust", "Medical Research Council", "Wellcome",
        "Biotechnology and Biological Sciences Research Council",
        "Engineering and Physical Sciences Research Council",
        "Cancer Research UK", "Health Data Research UK",
        "UK Research and Innovation", "UKRI",
    ],
    "EU": [
        "European Commission", "European Research Council",
        "Horizon 2020", "Horizon Europe",
        "Deutsche Forschungsgemeinschaft", "Agence nationale de la recherche",
        "Netherlands Organisation for Scientific Research",
    ],
}


def _classify_region(agency_name: str) -> str:
    for region, names in _REGION_MAP.items():
        for name in names:
            if name.lower() in agency_name.lower():
                return region
    return "Other"


def _region_pie_figure(agencies: list) -> go.Figure:
    if not agencies:
        return go.Figure().update_layout(title="No region data available")

    df = pd.DataFrame(agencies)
    df["region"] = df["agency"].apply(_classify_region)
    region_counts = df.groupby("region")["count"].sum().reset_index()
    region_counts.columns = ["region", "grants"]

    order = ["US", "UK", "EU", "Other"]
    region_counts["region"] = pd.Categorical(region_counts["region"], categories=order, ordered=True)
    region_counts = region_counts.sort_values("region")

    fig = px.pie(
        region_counts,
        names="region",
        values="grants",
        color="region",
        color_discrete_map={"US": "#1b75bb", "UK": "#e63946", "EU": "#2a9d8f", "Other": "#adb5bd"},
        template="simple_white",
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="%{label}<br>Grants: %{value}<br>Share: %{percent}<extra></extra>",
    )
    fig.update_layout(height=380, margin={"l": 20, "r": 20, "t": 30, "b": 20}, showlegend=True)
    return fig


def _kpi_card(value, label, color_class):
    return dbc.Card(
        dbc.CardBody(
            [
                html.H3(str(value), className="indicator-value"),
                html.Div(label, className="indicator-label"),
            ],
            className="indicator-card-body",
        ),
        className=f"indicator-card shadow-sm {color_class}",
    )


# ---------------------------------------------------------------------------
# Public layout builders
# ---------------------------------------------------------------------------

def get_publication_charts_section(entries_df, choropleth_fig=None):
    """
    Annual publications bar + global author distribution choropleth.
    Shared across funder + researcher personas; hidden by default.
    """
    annual_fig = _annual_publications_figure(entries_df)

    return html.Div(
        [
            html.Div("Publication Trends", className="section-title"),

            # Row 1: annual bar chart
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            html.Figure([
                                dcc.Graph(
                                    id="annual-publications-bar",
                                    figure=annual_fig,
                                    config={"displayModeBar": False},
                                ),
                                html.Figcaption(
                                    "Annual count of GA4GH-related publications indexed in Europe PMC.",
                                    style={"fontSize": "13px", "color": "#777", "marginTop": "6px"},
                                ),
                            ])
                        ),
                        className="mb-4 shadow-sm",
                        style={"borderRadius": "12px"},
                    ),
                    width=12,
                ),
                className="mb-2",
            ),

            # Row 2: full-width choropleth
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            html.Figure([
                                html.H5("Global Author Affiliation Distribution", style={"marginBottom": "6px"}),
                                dcc.Graph(
                                    id="epmc-countries-choropleth",
                                    figure=choropleth_fig or go.Figure(),
                                    config={"displayModeBar": False},
                                    style={"height": "650px"},
                                ),
                                html.Figcaption(
                                    "Each country's share (%) of total author affiliations across all GA4GH-related publications. Hover over a country to see its exact percentage.",
                                    style={"fontSize": "13px", "color": "#777", "marginTop": "6px"},
                                ),
                            ])
                        ),
                        className="mb-4 shadow-sm",
                        style={"borderRadius": "12px"},
                    ),
                    width=12,
                ),
            ),
        ],
        id="publication-charts",
        style={"display": "none"},
        className="epmc-section",
    )


def get_funder_only_charts_section(agencies_list):
    """
    Funder-specific charts: top agencies bar + region pie.
    Hidden by default; shown only when Funder persona is active.
    """
    agencies_fig = _top_agencies_figure(agencies_list)
    region_fig = _region_pie_figure(agencies_list)

    return html.Div(
        [
            html.Div("Funding Analytics", className="section-title"),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                html.Figure([
                                    html.H5("Top 15 Funding Agencies", style={"marginBottom": "8px"}),
                                    dcc.Graph(
                                        id="funder-top-agencies-bar",
                                        figure=agencies_fig,
                                        config={"displayModeBar": False},
                                    ),
                                    html.Figcaption(
                                        "Top 15 funding bodies by number of associated grants in the GA4GH publication dataset.",
                                        style={"fontSize": "13px", "color": "#777", "marginTop": "6px"},
                                    ),
                                ])
                            ),
                            className="mb-4 shadow-sm",
                            style={"borderRadius": "12px"},
                        ),
                        md=8,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                html.Figure([
                                    html.H5("Funders by Region", style={"marginBottom": "8px"}),
                                    dcc.Graph(
                                        id="funder-region-pie",
                                        figure=region_fig,
                                        config={"displayModeBar": False},
                                    ),
                                    html.Figcaption(
                                        "Grant distribution grouped by funder region (US, UK, EU, Other).",
                                        style={"fontSize": "13px", "color": "#777", "marginTop": "6px"},
                                    ),
                                ])
                            ),
                            className="mb-4 shadow-sm",
                            style={"borderRadius": "12px"},
                        ),
                        md=4,
                    ),
                ],
            ),
        ],
        id="funder-only-charts",
        style={"display": "none"},
        className="epmc-section",
    )

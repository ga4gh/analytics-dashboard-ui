import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import dcc, html

from app.utils.ga4gh_theme import FUNDING_COLORWAY, COLORS, chart_expand_button, chart_info_icon
from app.layouts.researcher_layout import _pub_type_figure, _open_access_figure
from app.constants.constants import STYLE_HEIGHT_3X

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

_REGION_COLORS = {
    "US": FUNDING_COLORWAY[0],
    "UK": FUNDING_COLORWAY[1],
    "EU": FUNDING_COLORWAY[2],
    "Other": FUNDING_COLORWAY[3],
}


def _classify_region(agency_name: str) -> str:
    for region, names in _REGION_MAP.items():
        for name in names:
            if name.lower() in agency_name.lower():
                return region
    return "Other"


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
        color_discrete_sequence=[COLORS["pink"]],
    )
    fig.update_traces(hovertemplate="Year: %{x}<br>Publications: %{y}<extra></extra>")
    fig.update_layout(
        height=380,
        margin={"l": 40, "r": 20, "t": 30, "b": 50},
        xaxis={"tickmode": "linear", "dtick": 1, "title": "Year"},
        yaxis={"title": "Number of Publications", "showgrid": True, "gridcolor": COLORS["lightgrey"]},
        bargap=0.25,
        hoverlabel=dict(font_color="white"),
    )
    return fig


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
        color_discrete_map=_REGION_COLORS,
        template="simple_white",
        hole=1/3,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        textfont_color="white",
        hovertemplate="%{label}<br>Grants: %{value}<br>Share: %{percent}<extra></extra>",
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
    Global author distribution choropleth. Shared across funder, researcher,
    and community personas; hidden by default.
    """
    return html.Div(
        [
            html.Div("Global Author Distribution", className="section-title"),
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            html.Figure([
                                chart_expand_button("epmc-countries-choropleth"),
                                html.Div([html.Span("Global Author Affiliation Distribution")] + chart_info_icon("epmc-countries-choropleth", "World map shaded by each country's share of total author affiliations across GA4GH-related publications. Darker shading indicates a higher proportion of affiliated authors."), className="chart-heading"),
                                dcc.Graph(
                                    id="epmc-countries-choropleth",
                                    figure=choropleth_fig or go.Figure(),
                                    style={"height": "650px"},
                                ),
                                dcc.Store(id="epmc-countries-choropleth-zoom-clamp-dummy"),
                                html.Figcaption(
                                    "Each country's share (%) of total author affiliations across all GA4GH-related publications. Hover over a country to see its exact percentage.",
                                    style={"color": COLORS["grey"], "marginTop": "6px"},
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


def get_funder_only_charts_section(agencies_list, entries_df=None, pub_types_list=None):
    """
    Combined publication & funding analytics: Funders by Region, Publication Types, Open Access.
    Hidden by default; shown when Funder, Researcher, or Community persona is active.
    """
    region_fig   = _region_pie_figure(agencies_list)
    pub_type_fig = _pub_type_figure(pub_types_list or [])
    oa_fig       = _open_access_figure(entries_df)

    def _pie_col(graph_id, title, tooltip, fig, figcaption):
        return dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    html.Figure([
                        chart_expand_button(graph_id),
                        html.Div([html.Span(title)] + chart_info_icon(graph_id, tooltip), className="chart-heading"),
                        dcc.Graph(
                            id=graph_id,
                            figure=fig,
                            className="chart-aspect-tall",
                            style={"height": STYLE_HEIGHT_3X},
                            config={"responsive": True},
                        ),
                        html.Figcaption(figcaption, style={"color": COLORS["grey"], "marginTop": "6px"}),
                    ])
                ),
                className="shadow-sm h-100 w-100",
                style={"borderRadius": "12px"},
            ),
            className="d-flex",
            md=4,
        )

    return html.Div(
        [
            html.Div("Publication & Funding Analytics", className="section-title"),
            dbc.Row(
                [
                    _pie_col(
                        "funder-region-pie",
                        "Funders by Region",
                        "Donut chart grouping funding agencies by geographic region (US, UK, EU, Other). Based on grant records linked to GA4GH-related publications in Europe PMC.",
                        region_fig,
                        "Grant distribution grouped by funder region (US, UK, EU, Other).",
                    ),
                    _pie_col(
                        "researcher-pub-type-donut",
                        "Publication Types",
                        "Breakdown of GA4GH-related publications by type — e.g. Journal Article, Review, Preprint. Each article is assigned one primary type; counts sum to the total unique article count.",
                        pub_type_fig,
                        "Each article is assigned one primary type — counts sum to the total unique article count.",
                    ),
                    _pie_col(
                        "researcher-oa-donut",
                        "Open Access Status",
                        "Proportion of GA4GH-related publications that are freely available as Open Access versus those that are restricted behind a paywall.",
                        oa_fig,
                        "Proportion of GA4GH-related publications available as open access.",
                    ),
                ],
                className="mb-4 chart-cards-row",
            ),
        ],
        id="funder-only-charts",
        style={"display": "none"},
        className="epmc-section",
    )

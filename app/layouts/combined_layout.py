"""Combined layout with four cumulative charts in one card."""

import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
from dash import dcc, html
from app.layouts.epmc_layout import make_citations_figure


def _build_source_year_df(df, year_col, item_col, source_name):
    """Return normalized [year, item, Source] rows for one source."""
    if df is None or df.empty or year_col not in df.columns or item_col not in df.columns:
        return pd.DataFrame(columns=["year", "item", "Source"])

    tmp = df[[year_col, item_col]].copy()
    tmp[year_col] = pd.to_numeric(tmp[year_col], errors="coerce")
    tmp[item_col] = tmp[item_col].fillna("").astype(str).str.strip()
    tmp = tmp.dropna(subset=[year_col])
    tmp = tmp[tmp[item_col] != ""]

    if tmp.empty:
        return pd.DataFrame(columns=["year", "item", "Source"])

    tmp["year"] = tmp[year_col].astype(int)
    tmp["item"] = tmp[item_col]
    tmp["Source"] = source_name
    return tmp[["year", "item", "Source"]]


def _make_source_growth_figure(source_year_df, source_name, line_color, yearly_label="New repos created", cumulative_label="Total repos to date"):
    """Build one cumulative growth chart for a single source."""
    if source_year_df is None or source_year_df.empty:
        return px.line(title=f"No {source_name} time-series data available")

    year_plot_df = (
        source_year_df.groupby("year", as_index=False)
        .agg({"item": list})
        .sort_values("year")
    )

    year_plot_df["items_str"] = year_plot_df["item"].apply(lambda items: "<br>".join(items))
    year_plot_df["yearly_count"] = year_plot_df["item"].apply(len)
    year_plot_df["yearly_cumulative_count"] = year_plot_df["yearly_count"].cumsum()

    fig = px.line(
        year_plot_df,
        x="year",
        y="yearly_cumulative_count",
        markers=True,
        title=source_name,
        labels={"year": "Year", "yearly_cumulative_count": "Cumulative Items"},
        custom_data=["items_str", "yearly_count"],
        template="simple_white",
    )

    fig.update_traces(
        marker={"size": 7, "color": line_color},
        line={"color": line_color},
        hovertemplate=(
            f"Year: %{{x}}<br>"
            f"{yearly_label}: %{{customdata[1]}}<br>"
            f"{cumulative_label}: %{{y}}<extra></extra>"
        ),
    )

    fig.update_layout(
        showlegend=False,
        height=430,
        margin={"l": 40, "r": 20, "t": 60, "b": 50},
        yaxis_title="Cumulative Items",
    )
    fig.update_xaxes(title_text="Year")
    return fig


def get_combined_layout(github_df, epmc_entries_df, pypi_first_releases_df, epmc_citations):
    """Build top-level combined chart layout for all three data sources."""
    gh_df = github_df.copy() if github_df is not None else pd.DataFrame()
    ep_df = epmc_entries_df.copy() if epmc_entries_df is not None else pd.DataFrame()
    py_df = pypi_first_releases_df.copy() if pypi_first_releases_df is not None else pd.DataFrame()

    if not gh_df.empty and "created_on" in gh_df.columns:
        gh_df["created_on_year"] = pd.to_datetime(gh_df["created_on"], errors="coerce", utc=True).dt.year

    if not py_df.empty and "release_date" in py_df.columns:
        py_df["release_year"] = pd.to_datetime(py_df["release_date"], errors="coerce", utc=True).dt.year

    github_year_df = _build_source_year_df(gh_df, "created_on_year", "name", "GitHub Repositories")
    epmc_year_df = _build_source_year_df(ep_df, "pub_year", "title", "GA4GH-Related Articles")
    pypi_year_df = _build_source_year_df(py_df, "release_year", "project_name", "PyPI Packages")

    gh_fig = _make_source_growth_figure(github_year_df, "GitHub Repositories", "#1b75bb")
    epmc_fig = _make_source_growth_figure(
        epmc_year_df, "GA4GH-Related Articles", "#e34a3a",
        yearly_label="New articles",
        cumulative_label="Total articles to date",
    )
    pypi_fig = _make_source_growth_figure(
        pypi_year_df, "PyPI Packages", "#9f79b0",
        yearly_label="New libraries created",
        cumulative_label="Total libraries to date",
    )

    citations_payload = epmc_citations if isinstance(epmc_citations, dict) else {}
    if isinstance(epmc_citations, list):
        citations_payload = {"citations_over_years": epmc_citations}
    citations_fig = make_citations_figure(citations_payload)
    citations_fig.update_layout(height=430, margin={"l": 40, "r": 20, "t": 70, "b": 60})

    return dbc.Card(
        dbc.CardBody(
            html.Figure([
                dbc.Row(
                    [    
                        dbc.Col(dcc.Graph(id="combined-growth-epmc", figure=epmc_fig), lg=6, md=6, sm=12),
                        dbc.Col(dcc.Graph(id="combined-citations-over-years", figure=citations_fig), lg=6, md=6, sm=12),
                        dbc.Col(dcc.Graph(id="combined-growth-github", figure=gh_fig), lg=6, md=6, sm=12),
                        dbc.Col(dcc.Graph(id="combined-growth-pypi", figure=pypi_fig), lg=6, md=6, sm=12),
                    ],
                    className="g-3",
                ),
                html.Figcaption("Cumulative number of GA4GH-Related Articles and their Citations from Europe PMC, as well as GitHub Repositories, and PyPI Packages per year.")
            ])
        ),
        className="mb-4 shadow-sm",
        style={"borderRadius": "12px"},
    )

"""Combined cross-source layout for cumulative yearly growth charts."""

import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
from dash import dcc


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


def _make_combined_growth_figure(github_df, epmc_df, pypi_first_releases_df):
    github_year_df = _build_source_year_df(github_df, "created_on_year", "name", "GitHub Repositories")
    epmc_year_df = _build_source_year_df(epmc_df, "pub_year", "title", "Europe PMC publications")
    pypi_year_df = _build_source_year_df(
        pypi_first_releases_df,
        "release_year",
        "project_name",
        "PyPi Libraries",
    )

    combined_year_df = pd.concat(
        [github_year_df, epmc_year_df, pypi_year_df],
        ignore_index=True,
    )

    if combined_year_df.empty:
        return px.line(title="No time-series data available")

    year_plot_df = (
        combined_year_df.groupby(["year", "Source"], as_index=False)
        .agg({"item": list})
        .sort_values(["Source", "year"])
    )

    year_plot_df["items_str"] = year_plot_df["item"].apply(lambda items: "<br>".join(items))
    year_plot_df["yearly_count"] = year_plot_df["item"].apply(len)
    year_plot_df["yearly_cumulative_count"] = year_plot_df.groupby("Source")["yearly_count"].cumsum()

    fig = px.line(
        year_plot_df,
        x="year",
        y="yearly_cumulative_count",
        color="Source",
        markers=True,
        title="Growth of GA4GH Resources Over Time",
        labels={"year": "Year", "yearly_cumulative_count": "Total to date"},
        custom_data=["items_str", "Source", "yearly_count"],
        template="simple_white",
    )

    fig.update_traces(marker={"size": 8})

    # Apply source-specific hover templates
    for trace in fig.data:
        source = trace.customdata[0][1] if trace.customdata is not None and len(trace.customdata) > 0 else ""
        if source == "Europe PMC publications":
            # Simplified hover for Europe PMC: year and article count only
            trace.hovertemplate = (
                "Year: %{x}<br>"
                "Articles published: %{customdata[2]}<br>"
                "Articles Published to Date: %{y}<extra></extra>"
            )
        else:
            # Detailed hover for other sources
            trace.hovertemplate = (
                "<b>%{customdata[1]}</b><br>"
                "Year: %{x}<br>"
                "Number of new items: %{customdata[2]}<br><br>"
                "<b>New Items:</b><br>%{customdata[0]}<extra></extra>"
            )

    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Cumulative Number of New Items",
        margin={"l": 40, "r": 20, "t": 70, "b": 120},
        height=600,
        legend_title_text="Resource Type",
    )

    return fig


def get_combined_layout(github_df, epmc_entries_df, pypi_first_releases_df):
    """Build top-level combined chart layout for all three data sources."""
    gh_df = github_df.copy() if github_df is not None else pd.DataFrame()
    ep_df = epmc_entries_df.copy() if epmc_entries_df is not None else pd.DataFrame()
    py_df = pypi_first_releases_df.copy() if pypi_first_releases_df is not None else pd.DataFrame()

    if not gh_df.empty and "created_on" in gh_df.columns:
        gh_df["created_on_year"] = pd.to_datetime(gh_df["created_on"], errors="coerce", utc=True).dt.year

    if not py_df.empty and "release_date" in py_df.columns:
        py_df["release_year"] = pd.to_datetime(py_df["release_date"], errors="coerce", utc=True).dt.year

    fig = _make_combined_growth_figure(gh_df, ep_df, py_df)

    return dbc.Card(
        dbc.CardBody(dcc.Graph(id="combined-growth-over-time", figure=fig)),
        className="mb-4 shadow-sm",
        style={"borderRadius": "12px"},
    )

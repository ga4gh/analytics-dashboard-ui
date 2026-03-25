"""
Dash callbacks for the EPMC analytics page.
Mirrors the pattern used by pypi_callbacks.py and github_callbacks.py.
"""

from dash import Input, Output
import dash_bootstrap_components as dbc
from dash import html
import pandas as pd
import json

from app.services.epmc_client import prepare_epmc_data, get_top_authors
from app.layouts.epmc_layout import (
    fig_epmc_countries_pie,
    fig_epmc_top_authors_bar,
)


def register_epmc_callbacks(app):
    """Register all EPMC-related Dash callbacks."""

    # Cache data at import-time so every callback shares the same frames.
    entries_df, countries_df, authors_df, total_entries = prepare_epmc_data()

    # chen needs to fix this – update column references once the real schema is known
    # These are the columns we expect to exist on entries_df for search / display.
    search_columns = [c for c in entries_df.columns] if not entries_df.empty else []

    # -----------------------
    # DataTable search
    # -----------------------
    @app.callback(
        Output("epmc-entries-table", "data"),
        Input("epmc-table-search", "value"),
    )
    def update_epmc_table(search_value):
        if entries_df.empty:
            return []
        if not search_value:
            return entries_df.to_dict("records")

        mask = entries_df[search_columns].apply(
            lambda col: col.astype(str).str.contains(search_value, case=False, na=False)
        ).any(axis=1)

        return entries_df[mask].to_dict("records")

    # -----------------------
    # Entry detail card on row select
    # -----------------------
    @app.callback(
        Output("epmc-entry-details", "children"),
        Input("epmc-entries-table", "selected_rows"),
    )
    def show_epmc_details(selected_rows):
        if not selected_rows or entries_df.empty:
            return dbc.Alert("Select an entry to see details", color="info")
        entry = entries_df.iloc[selected_rows[0]]

        # Parse the stored raw JSON object for richer fields
        raw = entry.get("raw_json") or "{}"
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
        except Exception:
            parsed = {}

        # Extract desired fields with sensible fallbacks
        abstract = parsed.get("abstract_text") or parsed.get("abstract") or "No abstract available"
        pub_year = entry.get("pub_year") or parsed.get("pub_year") or parsed.get("year") or "N/A"
        # affiliation may be a string or list
        aff = parsed.get("affiliation") or parsed.get("affiliations") or ""
        if isinstance(aff, list):
            affiliation = "; ".join([str(a) for a in aff if a]) or "N/A"
        else:
            affiliation = aff or "N/A"
        language = parsed.get("language") or parsed.get("lang") or "N/A"
        doi = entry.get("doi") or parsed.get("doi") or ""
        doi_url = f"https://doi.org/{doi}" if doi else None

        return dbc.Card([
            dbc.CardHeader(html.H4(entry.get("title", "N/A"))),
            dbc.CardBody([
                html.P(abstract),
                html.Hr(),
                html.P(f"Year: {pub_year}"),
                html.P(f"Affiliation: {affiliation}"),
                html.P(f"Language: {language}"),
                html.Br(),
                dbc.Button(
                    "View Article",
                    href=doi_url,
                    target="_blank",
                    color="primary",
                    className="me-2",
                    disabled=not doi_url,
                ),
            ]),
        ], style={"boxShadow": "0 4px 10px rgba(0,0,0,0.1)"})

    # -----------------------
    # Charts
    # -----------------------
    @app.callback(
        Output("epmc-countries-pie", "figure"),
        Output("epmc-authors-bar", "figure"),
        Input("epmc-top-n-slider", "value"),
    )
    def update_epmc_graphs(top_n):
        fig_pie = fig_epmc_countries_pie(countries_df)
        # Fetch top authors from backend with the requested count
        top_authors_data = get_top_authors(count=top_n)
        fig_bar = fig_epmc_top_authors_bar(top_authors_data, top_n=top_n)
        return fig_pie, fig_bar

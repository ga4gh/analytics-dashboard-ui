"""
Dash callbacks for the EPMC analytics page.
Mirrors the pattern used by pypi_callbacks.py and github_callbacks.py.
"""

from dash import Input, Output, dcc
import dash_bootstrap_components as dbc
from dash import html
import pandas as pd
import json
import re

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

    def get_filtered_sorted_df(search_value):
        """Apply same filtering/sorting logic as update_epmc_table."""
        if entries_df.empty:
            return pd.DataFrame()
        
        if not search_value:
            filtered = entries_df.copy()
        else:
            mask = entries_df[search_columns].apply(
                lambda col: col.astype(str).str.contains(search_value, case=False, na=False)
            ).any(axis=1)
            filtered = entries_df[mask].copy()
        
        # Sort by pub_year descending (most recent first)
        if "pub_year" in filtered.columns:
            filtered["_pub_year_num"] = pd.to_numeric(filtered["pub_year"], errors="coerce")
            filtered = filtered.sort_values(by=["_pub_year_num"], ascending=False).reset_index(drop=True)
            filtered = filtered.drop(columns=["_pub_year_num"])
        
        return filtered

    # -----------------------
    # DataTable search
    # -----------------------
    @app.callback(
        Output("epmc-entries-table", "data"),
        Input("epmc-table-search", "value"),
    )
    def update_epmc_table(search_value):
        filtered = get_filtered_sorted_df(search_value)
        return filtered.to_dict("records")

    # -----------------------
    # Entry detail card on row select
    # -----------------------
    @app.callback(
        Output("epmc-entry-details", "children"),
        Input("epmc-entries-table", "selected_rows"),
        Input("epmc-table-search", "value"),
    )
    def show_epmc_details(selected_rows, search_value):
        if not selected_rows or entries_df.empty:
            return dbc.Alert("Select an entry to see details", color="info")
        
        # Get the filtered/sorted data (same as displayed in table)
        filtered_df = get_filtered_sorted_df(search_value)
        if filtered_df.empty or selected_rows[0] >= len(filtered_df):
            return dbc.Alert("Select an entry to see details", color="info")
        
        entry = filtered_df.iloc[selected_rows[0]]

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

        # If abstract contains HTML tags, convert common HTML tags to Markdown
        # before rendering with `dcc.Markdown`. This avoids using
        # `dangerously_set_inner_html` which isn't supported in this Dash version.
        if isinstance(abstract, str) and ("<" in abstract and ">" in abstract):
            html_text = abstract
            # Headings: h1..h6 -> #..######
            for i in range(1, 7):
                html_text = re.sub(rf"<h{i}[^>]*>(.*?)</h{i}>", lambda m: "\n" + ("#" * i) + " " + m.group(1) + "\n", html_text, flags=re.I|re.S)

            # Line breaks and paragraphs
            html_text = re.sub(r"<br\s*/?>", "\n\n", html_text, flags=re.I)
            html_text = re.sub(r"<p[^>]*>", "\n\n", html_text, flags=re.I)
            html_text = re.sub(r"</p>", "\n\n", html_text, flags=re.I)

            # Emphasis and strong
            html_text = re.sub(r"<(?:i|em)[^>]*>(.*?)</(?:i|em)>", r"*\1*", html_text, flags=re.I|re.S)
            html_text = re.sub(r"<(?:b|strong)[^>]*>(.*?)</(?:b|strong)>", r"**\1**", html_text, flags=re.I|re.S)

            # Lists: convert <li> to markdown bullets
            html_text = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1\n", html_text, flags=re.I|re.S)

            # Remove any remaining tags
            html_text = re.sub(r"<[^>]+>", "", html_text)

            # Collapse multiple blank lines
            html_text = re.sub(r"\n{3,}", "\n\n", html_text)

            abstract_md = html_text.strip()
            if not abstract_md:
                abstract_md = "No abstract available"

            abstract_component = dcc.Markdown(abstract_md)
        else:
            abstract_component = html.P(abstract)

        return dbc.Card([
            dbc.CardHeader(html.H4(entry.get("title", "N/A"))),
            dbc.CardBody([
                abstract_component,
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

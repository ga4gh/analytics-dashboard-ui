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

from app.services.epmc_client import prepare_epmc_data, get_authors_by_article
from app.layouts.epmc_layout import (
    fig_epmc_countries_pie,
    fig_epmc_top_authors_bar,
)


def register_epmc_callbacks(app):
    """Register all EPMC-related Dash callbacks."""

    # Cache all data at import-time; prepare_epmc_data() fetches all APIs in one pass
    (entries_df, countries_df, authors_df, total_entries, 
     citations, unique_authors_count, top_authors_default) = prepare_epmc_data()

    search_columns = [c for c in entries_df.columns] if not entries_df.empty else []

    def normalize_affiliation_values(value):
        """Normalize affiliation value (string/list/dict) to list of strings."""
        aff_list = value if isinstance(value, list) else [value]
        normalized = []
        for item in aff_list:
            if isinstance(item, dict):
                text = item.get("name") or item.get("text") or item.get("label") or ""
            else:
                text = str(item) if item else ""
            text = text.strip() if isinstance(text, str) else ""
            if text:
                normalized.append(text)
        return normalized

    def get_filtered_sorted_df(search_value, year_filter=None, affiliation_filter=None):
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
        
        # Filter by pub_year dropdown
        if year_filter and "pub_year" in filtered.columns:
            filtered = filtered[filtered["pub_year"].astype(str) == str(year_filter)]
        
        if affiliation_filter and "raw_json" in filtered.columns:
            def _has_affiliation(raw):
                try:
                    obj = json.loads(raw) if isinstance(raw, str) else raw
                except Exception:
                    return False
                aff = obj.get("affiliation") or obj.get("affiliations") or ""
                if isinstance(aff, list):
                    aff = " ".join([str(a) for a in aff if a])
                return affiliation_filter.lower() in aff.lower()
            filtered = filtered[filtered["raw_json"].apply(_has_affiliation)]
        
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
        Input("epmc-year-filter", "value"),
        Input("epmc-affiliation-filter", "value"),
    )
    def update_epmc_table(search_value, year_filter, affiliation_filter):
        filtered = get_filtered_sorted_df(search_value, year_filter, affiliation_filter)
        return filtered.to_dict("records")

    # -----------------------
    # Entry detail card on row select
    # -----------------------
    @app.callback(
        Output("epmc-entry-details", "children"),
        Input("epmc-entries-table", "selected_rows"),
        Input("epmc-table-search", "value"),
        Input("epmc-year-filter", "value"),
        Input("epmc-affiliation-filter", "value"),
    )
    def show_epmc_details(selected_rows, search_value, year_filter, affiliation_filter):
        if not selected_rows or entries_df.empty:
            return dbc.Alert("Select an entry to see details", color="info")
        
        # Get the filtered/sorted data (same as displayed in table)
        filtered_df = get_filtered_sorted_df(search_value, year_filter, affiliation_filter)
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

        # Fetch authors lazily for the selected article only
        pm_id = (
            parsed.get("pm_id")
            or parsed.get("pmid")
            or parsed.get("pmId")
            or parsed.get("article_id")
            or parsed.get("id")
        )
        authors = get_authors_by_article(pm_id) if pm_id else []
        valid_authors = [a for a in authors if isinstance(a, dict)] if isinstance(authors, list) else []
        if valid_authors and any("author_order" in a for a in valid_authors):
            valid_authors = sorted(
                valid_authors,
                key=lambda a: (a.get("author_order") is None, a.get("author_order") or 0),
            )
        author_names = []
        for a in valid_authors:
            first = (a.get("firstname") or "").strip()
            last = (a.get("lastname") or "").strip()
            full = f"{first} {last}".strip() or (a.get("fullname") or "").strip()
            if full:
                author_names.append(full)
        authors_text = ", ".join(author_names) if author_names else "N/A"

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
                html.P(f"Authors: {authors_text}"),
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
    # Build initial charts from cached data
    # -----------------------
    @app.callback(
        Output("epmc-countries-pie", "figure"),
        Output("epmc-authors-bar", "figure"),
        Input("epmc-top-n-slider", "value"),  # Responds to slider but uses same cached authors
    )
    def update_epmc_graphs(top_n):
        fig_pie = fig_epmc_countries_pie(countries_df)
        # Use pre-fetched top_authors_default (no API call needed)
        fig_bar = fig_epmc_top_authors_bar(top_authors_default, top_n)
        return fig_pie, fig_bar

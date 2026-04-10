"""
Dash callbacks for the EPMC analytics page.
Mirrors the pattern used by pypi_callbacks.py and github_callbacks.py.
"""

from dash import Input, Output, State, dcc
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
        Output("first-author-store", "data"),
        Output("first-affiliation-store", "data"),
        Input("epmc-entries-table", "selected_rows"),
        Input("epmc-table-search", "value"),
        Input("epmc-year-filter", "value"),
        Input("epmc-affiliation-filter", "value"),
    )
    def show_epmc_details(selected_rows, search_value, year_filter, affiliation_filter):
        if not selected_rows or entries_df.empty:
            return dbc.Alert("Select an entry to see details", color="info"), None

        filtered_df = get_filtered_sorted_df(search_value, year_filter, affiliation_filter)
        if filtered_df.empty or selected_rows[0] >= len(filtered_df):
            return dbc.Alert("Select an entry to see details", color="info"), None

        entry = filtered_df.iloc[selected_rows[0]]

        raw = entry.get("raw_json") or "{}"
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
        except Exception:
            parsed = {}

        abstract = parsed.get("abstract_text") or parsed.get("abstract") or "No abstract available"
        pub_year = entry.get("pub_year") or parsed.get("pub_year") or parsed.get("year") or "N/A"
        language = parsed.get("language") or parsed.get("lang") or "N/A"
        doi = entry.get("doi") or parsed.get("doi") or ""
        doi_url = f"https://doi.org/{doi}" if doi else None

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

        # Build affiliation index: org_name -> number, and reverse map: number -> list of author names
        raw_affiliations = parsed.get("affiliations") or []
        affiliation_index = {}   # org_name -> aff_number
        affiliation_list = []    # list of (number, org_name)
        aff_counter = 1

        # First pass: build affiliation index
        if isinstance(raw_affiliations, list):
            for aff in sorted(raw_affiliations, key=lambda x: x.get("affiliation_order", 0)):
                org = aff.get("org_name", "").strip()
                if org and org not in affiliation_index:
                    affiliation_index[org] = aff_counter
                    affiliation_list.append((aff_counter, org))
                    aff_counter += 1

        # Build affiliation -> author names map
        author_id_to_name = {}
        for a in valid_authors:
            first = (a.get("firstname") or "").strip()
            last = (a.get("lastname") or "").strip()
            full = f"{first} {last}".strip() or (a.get("fullname") or "").strip()
            if full:
                author_id_to_name[a.get("id")] = full

        aff_to_authors = {}  # aff_number -> list of author names
        if isinstance(raw_affiliations, list):
            for aff in raw_affiliations:
                org = aff.get("org_name", "").strip()
                aid = aff.get("author_id")
                if org in affiliation_index and aid in author_id_to_name:
                    aff_num = affiliation_index[org]
                    if aff_num not in aff_to_authors:
                        aff_to_authors[aff_num] = []
                    author_name = author_id_to_name[aid]
                    if author_name not in aff_to_authors[aff_num]:
                        aff_to_authors[aff_num].append(author_name)

        # Build author items with superscript aff numbers
        author_id_to_affs = {}  # author_id -> list of aff numbers
        if isinstance(raw_affiliations, list):
            for aff in raw_affiliations:
                org = aff.get("org_name", "").strip()
                aid = aff.get("author_id")
                if org in affiliation_index and aid:
                    if aid not in author_id_to_affs:
                        author_id_to_affs[aid] = []
                    aff_num = affiliation_index[org]
                    if aff_num not in author_id_to_affs[aid]:
                        author_id_to_affs[aid].append(aff_num)

        author_items = []
        for a in valid_authors:
            first = (a.get("firstname") or "").strip()
            last = (a.get("lastname") or "").strip()
            full = f"{first} {last}".strip() or (a.get("fullname") or "").strip()
            if not full:
                continue
            aff_nums = author_id_to_affs.get(a.get("id"), [])
            superscript = f" {','.join(str("[") + str(n) + "]" for n in sorted(aff_nums))}" if aff_nums else ""
            author_items.append(f"{full}{superscript}")

        first_author_text = f"{author_items[0]}, et al." if len(author_items) > 1 else (author_items[0] if author_items else "N/A")
        all_authors_text = ", ".join(author_items) if author_items else "N/A"
        first_author_store = first_author_text

        # Build affiliation display items
        def aff_item(num, org):
            author_labels = ", ".join(aff_to_authors.get(num, []))
            return html.Div([
                html.Span(f"{num}. {org}", style={"fontSize": "14px"}),
                
            ], style={"marginBottom": "6px"})

        first_aff_component = aff_item(*affiliation_list[0]) if affiliation_list else html.P("N/A")
        rest_aff_components = [aff_item(num, org) for num, org in affiliation_list[1:]] if len(affiliation_list) > 1 else []

        # Abstract HTML to Markdown conversion
        if isinstance(abstract, str) and ("<" in abstract and ">" in abstract):
            html_text = abstract
            for i in range(1, 7):
                html_text = re.sub(rf"<h{i}[^>]*>(.*?)</h{i}>", lambda m: "\n" + ("#" * i) + " " + m.group(1) + "\n", html_text, flags=re.I|re.S)
            html_text = re.sub(r"<br\s*/?>", "\n\n", html_text, flags=re.I)
            html_text = re.sub(r"<p[^>]*>", "\n\n", html_text, flags=re.I)
            html_text = re.sub(r"</p>", "\n\n", html_text, flags=re.I)
            html_text = re.sub(r"<(?:i|em)[^>]*>(.*?)</(?:i|em)>", r"*\1*", html_text, flags=re.I|re.S)
            html_text = re.sub(r"<(?:b|strong)[^>]*>(.*?)</(?:b|strong)>", r"**\1**", html_text, flags=re.I|re.S)
            html_text = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1\n", html_text, flags=re.I|re.S)
            html_text = re.sub(r"<[^>]+>", "", html_text)
            html_text = re.sub(r"\n{3,}", "\n\n", html_text)
            abstract_md = html_text.strip() or "No abstract available"
            abstract_component = dcc.Markdown(abstract_md)
        else:
            abstract_component = html.P(abstract)

        card = dbc.Card([
            dbc.CardHeader(html.H4(entry.get("title", "N/A"))),
            dbc.CardBody([
                abstract_component,
                html.Hr(),
                html.P(f"Year: {pub_year}"),
                html.Hr(),

                # Authors collapsible
                html.H6("Authors: ", className="fw-bold"),
                
                html.Div([
                    html.Span("▶ ", style={"fontSize": "12px", "marginRight": "4px"}),
                    html.Span(first_author_text),
                ], id="author-collapse-button", n_clicks=0, style={
                    "color": "#0d9cf0",
                    "cursor": "pointer",
                    "fontWeight": "600",
                    "fontSize": "14px",
                    "display": "inline-flex",
                    "alignItems": "center",
                    "marginBottom": "0.5rem",
                }),
                dbc.Collapse(
                    html.P(all_authors_text, style={"fontSize": "14px", "color": "#555", "marginTop": "8px"}),
                    id="author-collapse",
                    is_open=False,
                ),
                html.Hr(),

                # Affiliations collapsible
                html.H6("Affiliations: ", className="fw-bold"),
                
                html.Div([
                    html.Span("▶ ", style={"fontSize": "12px", "marginRight": "4px"}),
                    html.Span("1. first_aff_component"),
                ], id="aff-collapse-button", n_clicks=0, style={
                    "color": "#0d9cf0",
                    "cursor": "pointer",
                    "fontWeight": "600",
                    "fontSize": "13px",
                    "display": "inline-flex" if rest_aff_components else "none",
                    "alignItems": "center",
                    "marginBottom": "0.5rem",
                }),
                dbc.Collapse(
                    html.Ul(rest_aff_components, style={"paddingLeft": "16px"}),
                    id="aff-collapse",
                    is_open=False,
                ),

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

        return card, first_author_store, first_aff_component

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
    
    @app.callback(
        Output("author-collapse", "is_open"),
        Output("author-collapse-button", "children"),
        Input("author-collapse-button", "n_clicks"),
        State("author-collapse", "is_open"),
        State("first-author-store", "data"),
    )
    def toggle_author_collapse(n, is_open, first_author):
        new_state = not is_open if n else is_open
        label = [
            html.Span("▼ " if new_state else "▶ ", style={"fontSize": "12px", "marginRight": "4px"}),
            html.Span(first_author or "Authors"),
        ]
        return new_state, label


    @app.callback(
        Output("aff-collapse", "is_open"),
        Output("aff-collapse-button", "children"),
        Input("aff-collapse-button", "n_clicks"),
        State("aff-collapse", "is_open"),
        State("first-affiliation-store", "data"),
    )
    def toggle_aff_collapse(n, is_open, first_affiliation):
        new_state = not is_open if n else is_open
        label = [
            html.Span("▼ " if new_state else "▶ ", style={"fontSize": "12px", "marginRight": "4px"}),
            html.Span(first_affiliation or "Affiliations"),
        ]
        return new_state, label

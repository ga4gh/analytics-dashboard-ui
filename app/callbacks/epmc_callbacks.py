from dash import Input, Output, State
import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
import json
import re
import plotly.express as px
import plotly.graph_objects as go

from app.services.epmc_client import prepare_epmc_data, get_affiliations_by_article
from app.constants.constants import COUNTRIES_WHITELIST


def fig_epmc_countries_pie(countries_df):
    """Pie chart – article count by affiliation country."""
    if countries_df is None or countries_df.empty:
        return go.Figure().update_layout(title="No country data available")

    cols = list(countries_df.columns)
    if "country" in [c.lower() for c in cols] and "count" in [c.lower() for c in cols]:
        country_col = next(c for c in cols if c.lower() == "country")
        count_col = next(c for c in cols if c.lower() == "count")
        df = countries_df[[country_col, count_col]].copy()
        df.columns = ["country", "count"]
    else:
        df = countries_df.iloc[:, :2].copy()
        df.columns = ["country", "count"]

    whitelist = {c.strip().lower() for c in COUNTRIES_WHITELIST}
    df["country_normalized"] = df["country"].astype(str).str.strip()
    df["country_lower"] = df["country_normalized"].str.lower()
    df = df[df["country_lower"].isin(whitelist)].copy()

    if df.empty:
        return go.Figure().update_layout(title="No country data available (after filtering)")

    counts = pd.to_numeric(df["count"], errors="coerce").fillna(0.0)
    total = counts.sum()
    if total <= 0:
        return go.Figure().update_layout(title="No country data available (zero total)")

    df = df.copy()
    df["count"] = counts
    df = df.sort_values("count", ascending=False).reset_index(drop=True)

    percents = (df["count"] / total * 100)
    slice_text = []
    hover_text = []
    for cn, cnt, pct in zip(df["country_normalized"], df["count"], percents):
        pct_fmt = f"{pct:.1f}%"
        if pct > 5.0:
            slice_text.append(f"{cn}<br>{pct_fmt}")
        else:
            slice_text.append(f"{pct_fmt}")
        hover_text.append(f"{cn}: {int(cnt)} ({pct_fmt})")

    text_positions = ["outside" if "<br>" in t else "inside" for t in slice_text]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=df["country_normalized"],
                values=df["count"],
                hole=0.2,
                text=slice_text,
                textinfo="text",
                hovertext=hover_text,
                hoverinfo="text",
                sort=False,
                textposition=text_positions,
                domain=dict(x=[0, 1], y=[0, 0.9]),
            )
        ]
    )
    fig.update_layout(
        title={"text": "Affiliation - Countries Represented", "x": 0.5},
        template="simple_white",
        height=700,
        margin=dict(l=20, r=20, t=80, b=80),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.1,
            xanchor="center",
            x=0.5,
        ),
    )
    return fig


def fig_epmc_top_authors_bar(authors_data, top_n=15):
    """Bar chart – top N authors by publication count."""
    if not authors_data:
        return go.Figure().update_layout(title="No author data available")

    df = pd.DataFrame(authors_data)
    if df.empty:
        return go.Figure().update_layout(title="No author data available")

    df = df.head(top_n).copy()
    df = df.sort_values("author_count", ascending=True)

    fig = px.bar(
        df,
        x="author_count",
        y="author",
        orientation="h",
        title=f"Top {top_n} Europe PMC Authors",
        template="simple_white",
        labels={"author_count": "Total Publication", "author": "Author Name"},
    )

    fig.update_traces(marker_line_width=0)
    fig.update_layout(
        yaxis=dict(automargin=True, tickfont=dict(size=9)),
        xaxis=dict(title="count"),
        margin=dict(l=240, r=40, t=60, b=40),
        height=max(400, 25 * len(df)),
        xaxis_title="Publication Count",
        yaxis_title="Author Name",
    )
    return fig


def build_most_cited_rows(entries_df):
    """Build rows for the Most Cited GA4GH Publications table."""
    most_cited_rows = []
    try:
        candidates = []
        if entries_df is not None and not entries_df.empty and "raw_json" in entries_df.columns:
            for raw in entries_df["raw_json"]:
                try:
                    obj = json.loads(raw)
                except Exception:
                    continue
                title = obj.get("title") or obj.get("name") or ""
                cited = obj.get("cited_by_count")
                try:
                    cited_count = int(cited) if cited is not None else 0
                except Exception:
                    cited_count = 0
                doi = obj.get("doi") or ""
                doi_url = f"https://doi.org/{doi}" if doi else None
                candidates.append({"title": title, "cited_by_count": cited_count, "doi_url": doi_url})

        if candidates:
            counts_df = pd.DataFrame.from_records(candidates)
            counts_df = counts_df.sort_values("cited_by_count", ascending=False).head(20)
            for _, row in counts_df.iterrows():
                doi_url = row.get("doi_url")
                title = str(row.get("title") or "")
                article_link = f"[View]({doi_url})" if doi_url else ""
                most_cited_rows.append(
                    {
                        "article_link": article_link,
                        "title": title,
                        "cited_by_count": int(row["cited_by_count"]),
                    }
                )
    except Exception:
        most_cited_rows = []
    return most_cited_rows


def register_epmc_callbacks(app):
    """Register all EPMC-related Dash callbacks."""

    # Cache all data at import-time; prepare_epmc_data() fetches all APIs in one pass
    (entries_df, countries_df, authors_df, total_entries, 
     citations, unique_authors_count, top_authors_default) = prepare_epmc_data()

    search_columns = [c for c in entries_df.columns] if not entries_df.empty else []

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

    @app.callback(
        Output("epmc-most-cited-table", "data"),
        Input("epmc-top-n-slider", "value"),
    )
    def update_most_cited_table(_top_n):
        return build_most_cited_rows(entries_df)

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
            return dbc.Alert("Select an entry to see details", color="info"), None, None

        filtered_df = get_filtered_sorted_df(search_value, year_filter, affiliation_filter)
        if filtered_df.empty or selected_rows[0] >= len(filtered_df):
            return dbc.Alert("Select an entry to see details", color="info"), None, None

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
        affiliation_rows = get_affiliations_by_article(pm_id) if pm_id else []
        affiliation_rows = [r for r in affiliation_rows if isinstance(r, dict)]
        affiliation_rows = sorted(
            affiliation_rows,
            key=lambda r: (
                r.get("author_order") is None,
                r.get("author_order") or 0,
                r.get("affiliation_order") is None,
                r.get("affiliation_order") or 0,
            ),
        )

        # Build ordered author map from affiliation rows
        author_order = []
        author_id_to_name = {}
        for row in affiliation_rows:
            aid = row.get("author_id")
            if aid is None:
                continue
            first = (row.get("firstname") or "").strip()
            last = (row.get("lastname") or "").strip()
            full = f"{first} {last}".strip() or (row.get("fullname") or "").strip()
            if not full:
                continue
            if aid not in author_id_to_name:
                author_id_to_name[aid] = full
                author_order.append(aid)

        # Build affiliation index and reverse map in affiliation order
        affiliation_index = {}
        affiliation_list = []
        for row in sorted(
            affiliation_rows,
            key=lambda r: (
                r.get("affiliation_order") is None,
                r.get("affiliation_order") or 0,
                r.get("author_order") is None,
                r.get("author_order") or 0,
            ),
        ):
            org = (row.get("org_name") or "").strip()
            if org and org not in affiliation_index:
                aff_num = len(affiliation_index) + 1
                affiliation_index[org] = aff_num
                affiliation_list.append((aff_num, org))

        aff_to_authors = {}
        author_id_to_affs = {}
        for row in affiliation_rows:
            aid = row.get("author_id")
            org = (row.get("org_name") or "").strip()
            if aid is None or org not in affiliation_index or aid not in author_id_to_name:
                continue

            aff_num = affiliation_index[org]
            author_name = author_id_to_name[aid]

            if aff_num not in aff_to_authors:
                aff_to_authors[aff_num] = []
            if author_name not in aff_to_authors[aff_num]:
                aff_to_authors[aff_num].append(author_name)

            if aid not in author_id_to_affs:
                author_id_to_affs[aid] = []
            if aff_num not in author_id_to_affs[aid]:
                author_id_to_affs[aid].append(aff_num)

        author_items = []
        for aid in author_order:
            full = author_id_to_name.get(aid)
            if not full:
                continue
            aff_nums = author_id_to_affs.get(aid, [])
            superscript = (" " + ",".join(f"[{n}]" for n in sorted(aff_nums))) if aff_nums else ""
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
        first_aff_text = f"{affiliation_list[0][0]}. {affiliation_list[0][1]}" if affiliation_list else "N/A"
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
                    first_aff_component,
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

        return card, first_author_store, first_aff_text

    # -----------------------
    # Build initial charts from cached data
    # -----------------------
    @app.callback(
        Output("epmc-countries-pie", "figure"),
        Output("epmc-authors-bar", "figure"),
        Output("epmc-authors-card-body", "style"),
        Input("epmc-top-n-slider", "value"),  # Responds to slider but uses same cached authors
    )
    def update_epmc_graphs(top_n):
        fig_pie = fig_epmc_countries_pie(countries_df)
        # Use pre-fetched top_authors_default (no API call needed)
        fig_bar = fig_epmc_top_authors_bar(top_authors_default, top_n)
        graph_height = max(400, 25 * min(top_n, len(top_authors_default)))
        return fig_pie, fig_bar, {"minHeight": f"{graph_height + 96}px"}
    
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

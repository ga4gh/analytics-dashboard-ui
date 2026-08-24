from dash import Input, Output, State, ALL, ctx, no_update
import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
import json
import re
import plotly.express as px
import plotly.graph_objects as go

from app.services.epmc_client import prepare_epmc_data, get_affiliations_by_article
from app.constants.constants import COUNTRIES_WHITELIST
from app.utils.ga4gh_theme import COLORWAY, COLORS, PUBLICATIONS_COLORWAY


def _prepare_countries_df(countries_df):
    """Shared column-normalize + whitelist-filter + sort for the countries
    pie and its legend — both must land on the exact same row order/set so
    legend swatches line up with pie slices and hidden_labels toggles agree."""
    if countries_df is None or countries_df.empty:
        return None

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
        return None

    df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(0.0)
    return df.sort_values("count", ascending=False).reset_index(drop=True)


def fig_epmc_countries_pie(countries_df, hidden_labels=None):
    """Pie chart – article count by affiliation country.

    hidden_labels: collection of country names currently toggled off in the
    legend.  Percentages are recalculated against the visible-only total so
    the displayed values stay correct after toggling.
    """
    df = _prepare_countries_df(countries_df)
    if df is None:
        return go.Figure().update_layout(title="No country data available")

    hidden = set(hidden_labels) if hidden_labels else set()
    visible_mask = ~df["country_normalized"].isin(hidden)
    visible_total = df.loc[visible_mask, "count"].sum()
    if visible_total <= 0:
        visible_total = df["count"].sum()
    if visible_total <= 0:
        return go.Figure().update_layout(title="No country data available (zero total)")

    slice_text = []
    hover_text = []
    for cn, cnt, is_vis in zip(df["country_normalized"], df["count"], visible_mask):
        if not is_vis:
            slice_text.append("")
            hover_text.append("")
        else:
            pct = cnt / visible_total * 100
            pct_fmt = f"{pct:.1f}%"
            if pct > 5.0:
                slice_text.append(f"{cn}<br>{pct_fmt}")
            else:
                slice_text.append(pct_fmt)
            hover_text.append(f"{cn}: {int(cnt)} ({pct_fmt})")

    # Always "inside", matching every other pie chart in the app (see
    # funder_layout.py / researcher_layout.py's textposition="inside") —
    # previously slices >5% (the top 3 countries) went "outside" instead.

    # Countries have no inherent "meaning" color (unlike e.g. a status of
    # Active/Inactive) and the slice count varies with the data, so this
    # cycles through the shared brand COLORWAY rather than a fixed mapping.
    slice_colors = [PUBLICATIONS_COLORWAY[i % len(PUBLICATIONS_COLORWAY)] for i in range(len(df))]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=df["country_normalized"],
                values=df["count"],
                hole=1/3,
                text=slice_text,
                textinfo="text",
                hovertext=hover_text,
                hoverinfo="text",
                sort=False,
                textposition="inside",
                insidetextfont=dict(color="white"),
                domain=dict(x=[0, 1], y=[0, 1]),
                marker=dict(colors=slice_colors),
            )
        ]
    )
    fig.update_layout(
        template="simple_white",
        # autosize (not a fixed height) + config={"responsive": True} on the
        # dcc.Graph + the .chart-aspect-square CSS class on that same graph
        # let the pie scale with the card's actual width at any viewport.
        autosize=True,
        margin=dict(l=0, r=0, t=0, b=0),
        # Plotly's own legend forces a scrollbar once a single legend passes
        # ~35 entries (this pie's country count), regardless of how much
        # space it's given — confirmed by testing at absurd margins/widths/
        # orientations, none of which disengage it. showlegend=False here;
        # build_countries_legend below renders a plain HTML replacement
        # instead, with clicks wired to the same hidden_labels mechanism.
        showlegend=False,
        hoverlabel=dict(font_color="white"),
    )
    if hidden:
        fig.update_layout(hiddenlabels=list(hidden))
    return fig


def build_countries_legend(countries_df, hidden_labels=None):
    """Custom HTML replacement for fig_epmc_countries_pie's legend.

    Mirrors the pie's own country order/colors exactly (same whitelist
    filter, same sort, same PUBLICATIONS_COLORWAY cycling) so swatches line
    up with their slices. Each item is independently clickable — toggling it
    in/out of epmc-countries-hidden-store, which both this function and
    fig_epmc_countries_pie read to stay in sync.
    """
    df = _prepare_countries_df(countries_df)
    if df is None:
        return []

    hidden = set(hidden_labels) if hidden_labels else set()

    items = []
    for i, cn in enumerate(df["country_normalized"]):
        color = PUBLICATIONS_COLORWAY[i % len(PUBLICATIONS_COLORWAY)]
        is_hidden = cn in hidden
        items.append(
            html.Button(
                [
                    html.Span(className="country-legend-swatch", style={"backgroundColor": color}),
                    html.Span(cn, className="country-legend-label"),
                ],
                id={"type": "country-legend-item", "country": cn},
                n_clicks=0,
                className="country-legend-item" + (" country-legend-item--hidden" if is_hidden else ""),
            )
        )
    return items


def fig_epmc_countries_choropleth(countries_df):
    """Choropleth world map — each country's % share of total author affiliations."""
    if countries_df is None or countries_df.empty:
        return go.Figure().update_layout(title="No country data available")

    cols = list(countries_df.columns)
    if "country" in [c.lower() for c in cols] and "count" in [c.lower() for c in cols]:
        country_col = next(c for c in cols if c.lower() == "country")
        count_col   = next(c for c in cols if c.lower() == "count")
        df = countries_df[[country_col, count_col]].copy()
        df.columns = ["country", "count"]
    else:
        df = countries_df.iloc[:, :2].copy()
        df.columns = ["country", "count"]

    whitelist = {c.strip().lower() for c in COUNTRIES_WHITELIST}
    df["country"] = df["country"].astype(str).str.strip()
    df = df[df["country"].str.lower().isin(whitelist)].copy()
    df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(0)

    if df.empty:
        return go.Figure().update_layout(title="No country data available")

    total = df["count"].sum()
    df["pct"] = (df["count"] / total * 100).round(2)
    df["hover_text"] = df.apply(
        lambda r: f"{r['country']}<br>{r['pct']}% of author affiliations", axis=1
    )

    # Brand-scaled gradient (white -> red) instead of Plotly's built-in
    # "Reds" scale, so the data-driven fill matches our own color system.
    fig = px.choropleth(
        df,
        locations="country",
        locationmode="country names",
        color="pct",
        color_continuous_scale=[COLORS["white"], COLORS["red"]],
        custom_data=["pct"],
        labels={"pct": "Share (%)", "country": "Country"},
        template="simple_white",
    )
    # Matches new_ga4gh's services-map.js D3 map exactly — can't reference the
    # CSS custom properties (--ga4gh-light-grey/--ga4gh-mid-grey/--faint-lightblue)
    # directly from a Plotly figure, same limitation their own JS comment notes
    # for its SCSS variables.
    fig.update_traces(
        hovertemplate="<b>%{location}</b><br>%{customdata[0]:.2f}% of author affiliations<extra></extra>",
        marker_line_color=COLORS["grey"],
        marker_line_width=0.5,
    )
    fig.update_layout(
        autosize=True,
        # t=28 reserves space for the floating modebar (camera/zoom/pan icons)
        # in the top-right corner — at t=0 the colorbar's own default len=1
        # matched the *full* plot area including that corner, so its title
        # ("Share (%)") rendered directly behind the modebar icons. With a
        # top margin, len=1 (still the default — unset here) now matches the
        # map's own visible container below that reserved strip instead.
        margin={"l": 0, "r": 0, "t": 28, "b": 0},
        coloraxis_colorbar={
            "title": "Share (%)",
            "thickness": 12,
            "ticksuffix": "%",
        },
        # bgcolor left at Plotly's default (matches each hovered point's own
        # scaled color, from white through to red) — only font color is set,
        # so text stays legible against whatever shade that point happens to be.
        hoverlabel=dict(font_color="white"),
    )
    fig.update_geos(
        showland=True,    landcolor=COLORS["lightgrey"],
        showocean=True,   oceancolor="rgba(79, 174, 220, 0.31)",
        showlakes=True,   lakecolor="rgba(79, 174, 220, 0.31)",
        showcountries=True, countrycolor=COLORS["grey"],
        projection_type="natural earth",
        showframe=False,
        # "Natural earth" is ~1.92:1 (w:h) — at this card's fixed height, the
        # full -90/90 lat range pillarboxes the map with empty side margins.
        # Cropping the (data-free) polar extremes lets the populated
        # landmass fill the card's width instead.
        lataxis_range=[-58, 85],
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
        template="simple_white",
        labels={"author_count": "Total Publication", "author": "Author Name"},
    )
    bar_colors = [PUBLICATIONS_COLORWAY[i % len(PUBLICATIONS_COLORWAY)] for i in range(len(df))]
    fig.update_traces(marker_line_width=0, marker_color=bar_colors)
    fig.update_layout(
        yaxis=dict(automargin=True, tickfont=dict(size=9)),
        xaxis=dict(title="count", showgrid=True, gridcolor=COLORS["lightgrey"]),
        margin=dict(l=240, r=40, t=20, b=40),
        height=max(400, 25 * len(df)),
        xaxis_title="Publication Count",
        yaxis_title="Author Name",
        hoverlabel=dict(font_color="white"),
    )
    return fig


def build_most_cited_rows(entries_df):
    """Build rows for the Most Cited GA4GH Publications table."""
    try:
        if entries_df is None or entries_df.empty:
            return []
        needed = {"title", "cited_by_count", "doi"}
        if not needed.issubset(entries_df.columns):
            return []
        df = entries_df[list(needed)].copy()
        df["cited_by_count"] = pd.to_numeric(df["cited_by_count"], errors="coerce").fillna(0).astype(int)
        df = df.sort_values("cited_by_count", ascending=False).head(20)
        rows = []
        for _, row in df.iterrows():
            doi = str(row.get("doi") or "")
            doi_url = f"https://doi.org/{doi}" if doi else None
            rows.append({
                "article_link":   f"[View]({doi_url})" if doi_url else "",
                "title":          str(row.get("title") or ""),
                "cited_by_count": int(row["cited_by_count"]),
            })
        return rows
    except Exception:
        return []


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
        
        if affiliation_filter and "affiliation" in filtered.columns:
            filtered = filtered[
                filtered["affiliation"].astype(str).str.contains(affiliation_filter, case=False, na=False)
            ]
        
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

        abstract  = entry.get("abstract_text") or "No abstract available"
        pub_year  = entry.get("pub_year") or "N/A"
        language  = entry.get("language") or "N/A"
        doi       = entry.get("doi") or ""
        doi_url   = f"https://doi.org/{doi}" if doi else None
        pm_id     = entry.get("pm_id") or None

        affiliation_rows = get_affiliations_by_article(pm_id) if pm_id else []
        affiliation_rows = [r for r in affiliation_rows if isinstance(r, dict)]

        def _row_display_affiliation_order(row):
            return row.get("display_affiliation_order") or row.get("affiliation_order")

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
                _row_display_affiliation_order(r) is None,
                _row_display_affiliation_order(r) or 0,
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
                    html.Span(first_author_text),
                    html.Span(className="methods-toggle-chevron"),
                ], id="author-collapse-button", n_clicks=0, className="methods-toggle", style={
                    "fontSize": "14px",
                    "marginBottom": "0.5rem",
                }),
                dbc.Collapse(
                    html.P(all_authors_text, style={"fontSize": "14px", "color": COLORS["dark"], "marginTop": "8px"}),
                    id="author-collapse",
                    is_open=False,
                ),
                html.Hr(),

                # Affiliations collapsible
                html.H6("Affiliations: ", className="fw-bold"),
                
                html.Div([
                    first_aff_component,
                    html.Span(className="methods-toggle-chevron", style={
                        "display": "inline-flex" if rest_aff_components else "none",
                    }),
                ], id="aff-collapse-button", n_clicks=0, className="methods-toggle", style={
                    "cursor": "pointer" if rest_aff_components else "default",
                    "fontSize": "13px",
                    "marginBottom": "0.5rem",
                }),
                dbc.Collapse(
                    html.Ul(rest_aff_components, style={"paddingLeft": "16px"}),
                    id="aff-collapse",
                    is_open=False,
                ),

                html.Br(),
                dbc.Button(
                    html.Span("View Article", className="btn-text"),
                    href=doi_url,
                    target="_blank",
                    className="ga4gh-btn-dark",
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
        Output("epmc-countries-legend", "children"),
        Output("epmc-authors-bar", "figure"),
        Output("epmc-authors-bar", "style"),
        Output("epmc-authors-card-body", "style"),
        Output("epmc-authors-bar-title", "children"),
        Input("epmc-top-n-slider", "value"),
        Input("epmc-countries-hidden-store", "data"),
    )
    def update_epmc_graphs(top_n, hidden_countries):
        # Legend-item click — only rebuild the pie + legend with updated percentages
        if ctx.triggered_id == "epmc-countries-hidden-store":
            return (
                fig_epmc_countries_pie(countries_df, hidden_labels=hidden_countries),
                build_countries_legend(countries_df, hidden_labels=hidden_countries),
                no_update, no_update, no_update, no_update,
            )

        fig_pie = fig_epmc_countries_pie(countries_df, hidden_labels=hidden_countries)
        legend_children = build_countries_legend(countries_df, hidden_labels=hidden_countries)
        fig_bar = fig_epmc_top_authors_bar(top_authors_default, top_n)
        # An explicit height directly on the Graph is required: dcc.Graph
        # renders in responsive mode (height:100%) with no CSS height of its
        # own, so it sizes off this card's ancestor container instead of its
        # own figure.layout.height — that indirection tracks growth fine but
        # never shrinks back down, since nothing ever forces the ancestor
        # smaller once Plotly's responsive engine has rendered it larger.
        graph_height = max(400, 25 * min(top_n, len(top_authors_default)))
        return (
            fig_pie,
            legend_children,
            fig_bar,
            {"height": f"{graph_height}px"},
            {"minHeight": f"{graph_height + 96}px"},
            f"Top {top_n} Europe PMC Authors",
        )

    @app.callback(
        Output("epmc-countries-hidden-store", "data"),
        Input({"type": "country-legend-item", "country": ALL}, "n_clicks"),
        State("epmc-countries-hidden-store", "data"),
        prevent_initial_call=True,
    )
    def toggle_country_legend_item(_n_clicks_list, hidden_data):
        # Despite prevent_initial_call=True, this pattern-matching ALL
        # callback still fires once (reproduced: twice, in fact) the moment
        # update_epmc_graphs first populates the 35 legend buttons — every
        # n_clicks is still 0 then, but ctx.triggered lists all of them as
        # "triggered" and ctx.triggered_id arbitrarily resolves to the first
        # one, which would otherwise mark it hidden before any real click.
        # A genuine click's triggered entry always has value >= 1, so this
        # guard (not just "is there a triggered entry") is what actually
        # distinguishes a real click from that spurious mount-time firing.
        if not ctx.triggered or not ctx.triggered[0].get("value"):
            return no_update
        prop_id = ctx.triggered[0]["prop_id"].rsplit(".", 1)[0]
        try:
            triggered = json.loads(prop_id)
        except (ValueError, TypeError):
            return no_update
        if not isinstance(triggered, dict):
            return no_update
        country = triggered.get("country")
        hidden = set(hidden_data or [])
        if country in hidden:
            hidden.discard(country)
        else:
            hidden.add(country)
        return sorted(hidden)
    
    @app.callback(
        Output("author-collapse", "is_open"),
        Output("author-collapse-button", "children"),
        Input("author-collapse-button", "n_clicks"),
        State("author-collapse", "is_open"),
        State("first-author-store", "data"),
    )
    def toggle_author_collapse(n, is_open, first_author):
        new_state = not is_open if n else is_open
        chevron_class = "methods-toggle-chevron is-open" if new_state else "methods-toggle-chevron"
        label = [
            html.Span(first_author or "Authors"),
            html.Span(className=chevron_class),
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
        chevron_class = "methods-toggle-chevron is-open" if new_state else "methods-toggle-chevron"
        label = [
            html.Span(first_affiliation or "Affiliations"),
            html.Span(className=chevron_class),
        ]
        return new_state, label

    # -----------------------
    # Interactive YoY growth KPI
    # -----------------------
    @app.callback(
        Output("yoy-growth-value", "children"),
        Input("yoy-year-selector", "value"),
        State("yearly-pub-counts", "data"),
    )
    def update_yoy_growth(selected_year, yearly_counts):
        if not selected_year or not yearly_counts:
            return "N/A"
        curr = yearly_counts.get(str(selected_year)) or yearly_counts.get(selected_year)
        prev = yearly_counts.get(str(selected_year - 1)) or yearly_counts.get(selected_year - 1)
        if curr is None or prev is None or prev == 0:
            return "N/A"
        pct = round((curr - prev) / prev * 100, 1)
        return f"+{pct}%" if pct >= 0 else f"{pct}%"


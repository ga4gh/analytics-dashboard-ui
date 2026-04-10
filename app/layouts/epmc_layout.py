"""
Dash layout for the EPMC analytics page.
Mirrors the pattern used by pypi_layout.py and github_layout.py.
"""

import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc

# whitelist of countries to display
from app.constants.constants import COUNTRIES_WHITELIST


# ---------------------------------------------------------------------------
# Figures (called from callbacks to rebuild charts)
# ---------------------------------------------------------------------------

def fig_epmc_countries_pie(countries_df):
    """Pie chart – article count by affiliation country."""
    if countries_df is None or countries_df.empty:
        return go.Figure().update_layout(title="No country data available")

    # Determine country / count columns robustly
    cols = list(countries_df.columns)
    if "country" in [c.lower() for c in cols] and "count" in [c.lower() for c in cols]:
        # match actual column names (case-sensitive) by lowercasing lookup
        country_col = next(c for c in cols if c.lower() == "country")
        count_col = next(c for c in cols if c.lower() == "count")
        df = countries_df[[country_col, count_col]].copy()
        df.columns = ["country", "count"]
    else:
        # fallback: assume first col = country, second col = count
        df = countries_df.iloc[:, :2].copy()
        df.columns = ["country", "count"]

    # Normalize country names and filter against whitelist (case-insensitive)
    whitelist = {c.strip().lower() for c in COUNTRIES_WHITELIST}
    df["country_normalized"] = df["country"].astype(str).str.strip()
    df["country_lower"] = df["country_normalized"].str.lower()
    df = df[df["country_lower"].isin(whitelist)].copy()

    if df.empty:
        return go.Figure().update_layout(title="No country data available (after filtering)")

    # Build the pie: make the pie visually larger by decreasing hole and increasing height
    # Only show the country label next to a slice if its percent > 5%
    counts = pd.to_numeric(df["count"], errors="coerce").fillna(0.0)
    total = counts.sum()
    if total <= 0:
        return go.Figure().update_layout(title="No country data available (zero total)")

    # Attach numeric counts to dataframe and sort descending so the largest
    # slices appear first (decreasing size). We set sort=False on the Pie
    # trace so Plotly preserves the order we supply.
    df = df.copy()
    df["count"] = counts
    df = df.sort_values("count", ascending=False).reset_index(drop=True)

    percents = (df["count"] / total * 100)
    # prepare text with one decimal place for percent and show country for slices > 5%
    slice_text = []
    hover_text = []
    for cn, cnt, pct in zip(df["country_normalized"], df["count"], percents):
        pct_fmt = f"{pct:.1f}%"
        if pct > 5.0:
            slice_text.append(f"{cn}<br>{pct_fmt}")
            textpos = "outside"
        else:
            slice_text.append(f"{pct_fmt}")
            textpos = "inside"
        hover_text.append(f"{cn}: {int(cnt)} ({pct_fmt})")

    # compute textposition list (outside for labeled slices, inside otherwise)
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
                # make pie larger inside figure
                domain=dict(x=[0, 1], y=[0, 0.9])  # y max < 1 to leave space for legend
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
            x=0.5
        )
    )
    return fig


def fig_epmc_top_authors_bar(authors_data, top_n=15):
    """Bar chart – top N authors by publication count."""
    if not authors_data:
        return go.Figure().update_layout(title="No author data available")

    # Convert to DataFrame, take top_n, and sort ascending for horizontal bar
    df = pd.DataFrame(authors_data)
    if df.empty:
        return go.Figure().update_layout(title="No author data available")

    # Take top_n and sort ascending so largest appears at top
    df = df.head(top_n).copy()
    df = df.sort_values("author_count", ascending=True)

    labels = {
        "author_count": "Total Publication",
        "author": "Author Name",
    }

    fig = px.bar(
        df,
        x="author_count",
        y="author",
        orientation="h",
        title=f"Top {top_n} Europe PMC Authors",
        template="simple_white",
        labels=labels,
    )

    fig.update_traces(marker_line_width=0)
    fig.update_layout(
        yaxis=dict(
            automargin=True,
            tickfont=dict(size=9),
        ),
        xaxis=dict(title="count"),
        margin=dict(l=240, r=40, t=60, b=40),
        height=max(400, 25 * len(df)),
        xaxis_title = "Publication Count",
        yaxis_title = "Author Name",
    )

    return fig


def make_citations_figure(data):
    citations_over_years = data.get("citations_over_years", [])
    
    filtered = [r for r in citations_over_years if r.get("pub_year") and r.get("pub_year") > 2013]
    years = [r.get("pub_year") for r in filtered]
    year_counts = [r.get("year_count") for r in filtered]
    cumulative_counts = [r.get("commulative_count") for r in filtered]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=years,
            y=cumulative_counts,
            mode="lines+markers",
            name="Cumulative Citations",
            line={"color": "#2ECC71"},
            marker={"size": 7, "color": "#2ECC71"},
            customdata=list(zip(year_counts)),
            hovertemplate=(
                "Year: %{x}<br>"
                "New citations: %{customdata[0]}<br>"
                "Total citations to date: %{y}<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title="Europe PMC Cumulative Citations Per Year",
        xaxis_title="Year",
        yaxis_title="Cumulative Citations",
        template="simple_white"
    )

    return fig


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

def get_epmc_layout(entries_df, countries_df, authors_df, total_entries, citations):
    """
    Build and return the full EPMC page layout using cached data (no additional API calls).
    """
    # Compute most-cited publications inline using `cited_by_count` from entries_df
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
                # prefer explicit cited_by_count field, fall back to 0
                cited = obj.get("cited_by_count")
                try:
                    cited_count = int(cited) if cited is not None else 0
                except Exception:
                    cited_count = 0
                doi = obj.get("doi") or ""
                doi_url = f"https://doi.org/{doi}" if doi else None
                candidates.append({"title": title, "cited_by_count": cited_count, "doi_url": doi_url})

        # sort descending and take top 20
        if candidates:
            counts_df = pd.DataFrame.from_records(candidates)
            counts_df = counts_df.sort_values("cited_by_count", ascending=False).head(20)
            for _, r in counts_df.iterrows():
                doi_url = r.get("doi_url")
                title = str(r.get("title") or "")
                article_link = f"[View]({doi_url})" if doi_url else ""
                most_cited_rows.append(
                    {
                        "article_link": article_link,
                        "title": title,
                        "cited_by_count": int(r["cited_by_count"]),
                    }
                )
    except Exception:
        most_cited_rows = []
    return dbc.Container(
        [


            # ---------- FILTERS ----------
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Top Authors"),
                            dcc.Slider(
                                id="epmc-top-n-slider",
                                min=5,
                                max=50,
                                step=5,
                                value=15,
                                marks={i: str(i) for i in range(5, 55, 5)},
                                tooltip={
                                    "placement": "bottom",
                                    "always_visible": True,
                                },
                            ),
                        ],
                        style={"width": "50%"},
                    ),
                ],
                style={
                    "display": "flex",
                    "gap": "20px",
                    "marginTop": "20px",
                    "marginBottom": "20px",
                },
            ),

            # ---------- GRAPHS  ----------
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                html.Figure([
                                    dcc.Graph(id="epmc-authors-bar"),
                                    html.Figcaption("Bar chart of the number of GA4GH-related articles authored by the top individuals.")
                                ])
                            ),
                            className="mb-4 shadow-sm",
                            style={"borderRadius": "12px"},
                        ),
                        md=12,
                    ),
                ]
            ),
            # Countries pie + Most-cited publications side-by-side
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                html.Figure([
                                    dcc.Graph(id="epmc-countries-pie"),
                                    html.Figcaption("Relative proportion of country affiliations for all authors of GA4GH-related articles. Country affiliation is determined from each author’s affiliation for all publications.")
                                ])
                            ),
                            className="mb-4 shadow-sm h-100 w-100",
                            style={"borderRadius": "12px"},
                        ),
                        className="d-flex",
                        md=6,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                html.Div(
                                    [
                                        html.H5("Most Cited GA4GH Publications", style={"marginBottom": "12px"}),
                                        html.Figcaption("Table of the most cited GA4GH-related articles, sorted in descending order by number of citations.", style={"marginBottom": "12px"}),
                                        html.Div(
                                            dash_table.DataTable(
                                                id="epmc-most-cited-table",
                                                columns=[
                                                    {"name": "Article", "id": "article_link", "presentation": "markdown"},
                                                    {"name": "Title", "id": "title"},
                                                    {"name": "Citations", "id": "cited_by_count"},
                                                ],
                                                data=most_cited_rows,
                                                page_size=20,
                                                style_table={"height": "100%", "overflowX": "auto", "overflowY": "auto"},
                                                style_cell={
                                                    "textAlign": "left",
                                                    "padding": "4px 6px",
                                                    "fontSize": "13px",
                                                    "lineHeight": "1.15",
                                                    "fontFamily": "'Proxima Nova', 'ProximaNova', 'Helvetica Neue', Arial, sans-serif",
                                                    "whiteSpace": "normal",
                                                },
                                                style_header={
                                                    "backgroundColor": "#2c3e50",
                                                    "color": "white",
                                                    "fontWeight": "bold",
                                                    "padding": "5px 6px",
                                                    "fontFamily": "'Proxima Nova', 'ProximaNova', 'Helvetica Neue', Arial, sans-serif",
                                                },
                                                style_data_conditional=[
                                                    {"if": {"column_id": "article_link"}, "width": "8%", "textAlign": "center"},
                                                    {"if": {"column_id": "title"}, "width": "76%"},
                                                    {"if": {"column_id": "cited_by_count"}, "width": "16%", "textAlign": "right"},
                                                ],
                                                css=[
                                                    {"selector": ".dash-cell-value p", "rule": "margin: 0; line-height: 1.1;"},
                                                    {"selector": "td[data-dash-column='article_link'] a", "rule": "display:inline-block; padding:2px 8px; border:1px solid #0d6efd; background-color:#0d6efd; color:#fff; border-radius:0.375rem; text-decoration:none; font-size:12px; font-weight:500; line-height:1.1;"},
                                                ],
                                                markdown_options={"link_target": "_blank"},
                                            ),
                                            style={"flex": "1 1 auto", "minHeight": 0},
                                        ),
                                    ],
                                    style={"display": "flex", "flexDirection": "column", "height": "100%"}
                                )
                            , style={"height": "100%"}),
                            className="mb-4 shadow-sm h-100 w-100 epmc-most-cited-card",
                            style={"borderRadius": "12px"},
                        ),
                        className="d-flex",
                        md=6,
                    ),
                ]
            ),


        ],
        fluid=True,
    )

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

    percents = (df["count"] / total * 100).round(1)
    # text: show country name only for slices > 5%, otherwise empty string
    text_labels = [cn if p > 5.0 else "" for cn, p in zip(df["country_normalized"], percents)]
    # textposition: put text outside for labeled slices, inside for unlabeled (will only show percent)
    text_positions = ["outside" if t else "inside" for t in text_labels]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=df["country_normalized"],
                values=df["count"],
                hole=0.2,  # smaller hole → bigger pie
                text=text_labels,
                textinfo="percent+text",
                hoverinfo="label+value+percent",
                sort=False,
                textposition=text_positions,
            )
        ]
    )
    fig.update_layout(
        title={"text": "Affiliation Countries Represented", "x": 0.5},
        template="simple_white",
        height=700,
        margin=dict(l=20, r=20, t=80, b=20),
    )
    return fig


def fig_epmc_top_authors_bar(authors_data, top_n=30):
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


def get_citations_by_year(data: dict) -> list[dict]:
    """Aggregate citations by pub_year, counting entries per year."""
    citations = data.get("citations", []) if isinstance(data, dict) else []
    if not citations:
        return []
    
    counts_by_year = {}
    for row in citations:
        py = row.get("pub_year")
        if py is not None:
            counts_by_year[py] = counts_by_year.get(py, 0) + 1
    
    return [{"pub_year": year, "total_citations": count} for year, count in sorted(counts_by_year.items())]


def make_citations_figure(data):
    result = get_citations_by_year(data)
    print(result)
    years = [r["pub_year"] for r in result]
    totals = [r["total_citations"] for r in result]
    
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=years,
            y=totals,
            mode="lines+markers",
            name="Citations"
        )
    )

    fig.update_layout(
        title="Europe PMC Citations Per Year",
        xaxis_title="Year",
        yaxis_title="Citations Count",
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
    # Compute most-cited publications inline (no separate helper function)
    most_cited_children = []
    # Normalize citations payload (accept list or dict containing list)
    uc_list = []
    if isinstance(citations, list):
        uc_list = citations
    elif isinstance(citations, dict):
        for k in ("results", "items", "citations", "data"):
            if k in citations and isinstance(citations[k], list):
                uc_list = citations[k]
                break

    uc_df = pd.DataFrame.from_records(uc_list) if uc_list else pd.DataFrame()
    if not uc_df.empty and "article_id" in uc_df.columns:
            # Count unique citations per article_id (prefer unique citation_id)
            if "citation_id" in uc_df.columns:
                counts = uc_df.groupby(uc_df["article_id"].astype(str))["citation_id"].nunique()
            else:
                counts = uc_df["article_id"].astype(str).value_counts()
            counts_df = counts.reset_index()
            counts_df.columns = ["article_id", "citation_count"]
            
            # Map article_id to title from entries_df
            titles_map = {}
            if entries_df is not None and not entries_df.empty and "raw_json" in entries_df.columns:
                for raw in entries_df["raw_json"]:
                    try:
                        obj = json.loads(raw)
                        aid = str(obj.get("id") or obj.get("article_id") or "")
                        if aid:
                            titles_map[aid] = obj.get("title") or obj.get("name") or aid
                    except Exception:
                        pass
            
            counts_df["title"] = counts_df["article_id"].map(lambda x: titles_map.get(x, x))
            counts_df = counts_df.sort_values("citation_count", ascending=False).head(20)
            
            for _, r in counts_df.iterrows():
                most_cited_children.append(
                    html.Div(f"{r['title']} — {int(r['citation_count'])}", 
                            style={"marginBottom": "8px", "fontSize": "14px"})
                )
    
    if not most_cited_children:
        most_cited_children.append(html.Div("No citation data available", style={"fontSize": "14px"}))
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
                        style={"width": "45%"},
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
                            dbc.CardBody(dcc.Graph(id="epmc-authors-bar")),
                            className="mb-4 shadow-sm",
                            style={"borderRadius": "12px"},
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(dcc.Graph(
                                id = "epmc-citations-over-years",
                                figure = make_citations_figure(citations)
                            )),
                            className="mb-4 shadow-sm",
                            style={"borderRadius": "12px"},
                        ),
                        md=6,
                    ),
                ]
            ),
            # Countries pie + Most-cited publications side-by-side
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(dcc.Graph(id="epmc-countries-pie")),
                            className="mb-4 shadow-sm",
                            style={"borderRadius": "12px"},
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                # build a simple vertical list of "Title — count"
                                html.Div(
                                    [
                                        html.H5("Most Cited GA4GH Publications", style={"marginBottom": "12px"}),
                                        html.Div(
                                            most_cited_children,
                                            id="epmc-most-cited-list",
                                            style={"maxHeight": "420px", "overflowY": "auto"},
                                        ),
                                    ]
                                )
                            ),
                            className="mb-4 shadow-sm",
                            style={"borderRadius": "12px"},
                        ),
                        md=6,
                    ),
                ]
            ),


        ],
        fluid=True,
    )

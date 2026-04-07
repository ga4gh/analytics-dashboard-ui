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

    # compute cumulative totals
    cumulative = []
    running = 0
    for t in totals:
        try:
            running += int(t)
        except Exception:
            running += 0
        cumulative.append(running)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=years,
            y=cumulative,
            mode="lines+markers",
            name="Cumulative Citations"
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
    most_cited_children = []
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
                candidates.append({"title": title, "cited_by_count": cited_count})

        # sort descending and take top 20
        if candidates:
            counts_df = pd.DataFrame.from_records(candidates)
            counts_df = counts_df.sort_values("cited_by_count", ascending=False).head(20)
            for _, r in counts_df.iterrows():
                most_cited_children.append(
                    html.Div(f"{r['title']} — {int(r['cited_by_count'])}", style={"marginBottom": "8px", "fontSize": "14px"})
                )
    except Exception:
        most_cited_children = []

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
                                            style={"overflowY": "auto", "flex": "1 1 auto", "paddingRight": "8px"},
                                        ),
                                    ],
                                    style={"display": "flex", "flexDirection": "column", "height": "100%"}
                                )
                            ),
                            className="mb-4 shadow-sm",
                            style={"borderRadius": "12px", "height": "700px"},
                        ),
                        md=6,
                    ),
                ]
            ),


        ],
        fluid=True,
    )

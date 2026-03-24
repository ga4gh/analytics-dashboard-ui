"""
Dash layout for the EPMC Test analytics page.
Mirrors the pattern used by pypi_layout.py and github_layout.py.
"""

import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from dash import html, dcc, dash_table
import pandas as pd

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

    percents = counts / total * 100.0
    # text: show country name only for slices > 5%, otherwise empty string
    text_labels = [cn if p > 5.0 else "" for cn, p in zip(df["country_normalized"], percents)]
    # textposition: put text outside for labeled slices, inside for unlabeled (will only show percent)
    text_positions = ["outside" if t else "inside" for t in text_labels]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=df["country_normalized"],
                values=counts,
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
        title={"text": "Affiliation Countries Distribution", "x": 0.5},
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

    fig = px.bar(
        df,
        x="author_count",
        y="author",
        orientation="h",
        title=f"Top {top_n} PMC Authors",
        template="simple_white",
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
    )

    return fig


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

def get_epmc_layout(entries_df, countries_df, authors_df, total_entries):
    """
    Build and return the full EPMC Test page layout.
    """
    # Ensure we have a DataFrame even if data is missing
    if entries_df is None or (isinstance(entries_df, pd.DataFrame) and entries_df.empty):
        entries_df = pd.DataFrame(columns=[
            "pmcid", "title", "author", "journal", "publish_date", "affiliation_country"
        ])
        # chen needs to fix this – update column list once schema is finalised

    return dbc.Container(
        [
            # ---------- TITLE ----------
            html.H1(
                "EPMC Test Dashboard",
                style={
                    "textAlign": "center",
                    "marginTop": "20px",
                    "marginBottom": "10px",
                    "fontSize": "60px",
                    "fontWeight": "bold",
                    "color": "#2C3E50",
                    "textShadow": "2px 2px #BDC3C7",
                },
            ),

            html.H2(
                f"Total EPMC Entries: {total_entries}",
                style={
                    "textAlign": "center",
                    "margin-bottom": "20px",
                    "color": "#9DAAB8",
                },
            ),

            # ---------- SEARCH ----------
            dcc.Input(
                id="epmc-table-search",
                type="text",
                placeholder="Search entries...",
                debounce=False,
                style={
                    "margin-bottom": "15px",
                    "width": "350px",
                    "padding": "8px",
                    "border-radius": "5px",
                    "border": "1px solid #ccc",
                },
            ),

            # ---------- TABLE + DETAILS ----------
            dbc.Row(
                [
                    # LEFT: table
                    dbc.Col(
                        [
                            dash_table.DataTable(
                                id="epmc-entries-table",
                                # chen needs to fix this – update columns to match real schema
                                columns=[
                                    {"name": "PMC ID", "id": "pmcid"},
                                    {"name": "Title", "id": "title"},
                                    {"name": "Journal", "id": "journal"},
                                ],
                                data=entries_df.to_dict("records") if not entries_df.empty else [],
                                row_selectable="single",
                                page_size=10,
                                sort_action="native",
                                style_table={"overflowX": "auto"},
                                style_cell={
                                    "textAlign": "left",
                                    "padding": "10px",
                                    "whiteSpace": "normal",
                                },
                                style_header={
                                    "backgroundColor": "#2c3e50",
                                    "color": "white",
                                    "fontWeight": "bold",
                                },
                            )
                        ],
                        width=6,
                    ),
                    # RIGHT: detail card
                    dbc.Col(html.Div(id="epmc-entry-details"), width=6),
                ],
            ),

            # ---------- FILTERS ----------
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Top N Authors"),
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
                        style={"width": "60%"},
                    ),
                ],
                style={
                    "display": "flex",
                    "gap": "20px",
                    "marginTop": "20px",
                    "marginBottom": "20px",
                },
            ),

            # ---------- GRAPHS ----------
            dbc.Card(
                dbc.CardBody(dcc.Graph(id="epmc-authors-bar")),
                className="mb-4 shadow-sm",
                style={"borderRadius": "12px"},
            ),
            dbc.Card(
                dbc.CardBody(dcc.Graph(id="epmc-countries-pie")),
                className="mb-4 shadow-sm",
                style={"borderRadius": "12px"},
            ),            
        ],
        fluid=True,
    )

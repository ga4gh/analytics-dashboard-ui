# ga4gh_theme.py
from typing import Optional
import plotly.graph_objects as go
import plotly.io as pio
from dash import html
import dash_bootstrap_components as dbc

# ------------------------------------------------------------------
# COLORS
# ------------------------------------------------------------------
COLORS = {
    "heroblue": "#01266a",
    "darkblue": "#1b75bb",
    "lightblue": "#4faedc",
    "purple": "#9f79b0",
    "orange": "#faa633",
    "red": "#e34a3a",
    "green": "#8cc63e",
    "darkgreen": "#00a99d",
    "secondary_blue": "#6492BE",
    "secondary_orange": "#F15B27",
    "pink": "#ED2079",
    "secondary_purple": "#A72176",
    "midnight_blue": "#01225f",
    "mamba": "#9c879b",
    "forest_green": "#4a7c2e",
    # Light variants — second pass of COLORWAY past 14 categories.
    "darkblue_light": "#8dbadd",
    "green_light": "#c6e29e",
    "red_light": "#f1a49c",
    "lightblue_light": "#a7d6ee",
    "orange_light": "#fcd299",
    "purple_light": "#cfbcd8",
    "secondary_blue_light": "#b2c8de",
    "darkgreen_light": "#80d4ce",
    "pink_light": "#f690bc",
    "midnight_blue_light": "#8090af",
    "secondary_orange_light": "#f8ad93",
    "secondary_purple_light": "#d390ba",
    "mamba_light": "#cec3cd",
    "forest_green_light": "#a4be96",
    
    "lightgrey": "#efefef",
    "grey": "#767676",
    "dark": "#363636",
    "white": "#ffffff",
    "black": "#000000",
}

# ------------------------------------------------------------------
# COLOR SEQUENCE
# ------------------------------------------------------------------
# Shared colorway for any multi-category chart; repeats as lighter tints past 14.
COLORWAY = [
    COLORS["darkblue"],
    COLORS["green"],
    COLORS["red"],
    COLORS["lightblue"],
    COLORS["orange"],
    COLORS["purple"],
    COLORS["secondary_blue"],
    COLORS["darkgreen"],
    COLORS["pink"],
    COLORS["midnight_blue"],
    COLORS["secondary_orange"],
    COLORS["secondary_purple"],
    COLORS["mamba"],
    COLORS["forest_green"],
    COLORS["darkblue_light"],
    COLORS["green_light"],
    COLORS["red_light"],
    COLORS["lightblue_light"],
    COLORS["orange_light"],
    COLORS["purple_light"],
    COLORS["secondary_blue_light"],
    COLORS["darkgreen_light"],
    COLORS["pink_light"],
    COLORS["midnight_blue_light"],
    COLORS["secondary_orange_light"],
    COLORS["secondary_purple_light"],
    COLORS["mamba_light"],
    COLORS["forest_green_light"],
]

# ------------------------------------------------------------------
# SECTION SINGLE COLORS
# ------------------------------------------------------------------
PUBLICATIONS_COLOR = COLORS["red"]
GITHUB_COLOR = COLORS["orange"]
PYPI_COLOR = COLORS["purple"]
IMPLEMENTATIONS_COLOR = COLORS["darkblue"]

# ------------------------------------------------------------------
# HEATMAP / CHOROPLETH COLOR SCALE
# ------------------------------------------------------------------
# darkblue excluded deliberately: reserved for "no data" countries' landcolor.
HEATMAP_COLORWAY = [
    COLORS["white"],
    COLORS["orange"],
    COLORS["red"],
    COLORS["purple"],
]

# Fixed per-workstream colors so a given workstream renders the same color on
# every GitHub chart, regardless of sort order or which filter is active.
WORKSTREAM_COLORS = {
    "Genomic Knowledge Standards":      COLORS["orange"],
    "Tech/TASC":                        COLORS["darkblue"],
    "Cloud":                            COLORS["lightblue"],
    "Large Scale Genomics":             COLORS["green"],
    "Clinical and Phenotypic":          COLORS["secondary_purple"],
    "Data Discovery":                   COLORS["purple"],
    "Regulatory and Ethics":            COLORS["red"],
    "Data Security":                    COLORS["darkgreen"],
    "Data Use and Researcher Identity": COLORS["pink"],
}

# ------------------------------------------------------------------
# CHART EXPAND-TO-MODAL BUTTON
# ------------------------------------------------------------------
def chart_info_icon(graph_id: str, tooltip_text: str) -> list:
    """
    Returns [bi icon element, dbc.Tooltip] to splice into a chart-heading div.
    Uses Bootstrap Icons bi-info-circle-fill (requires Bootstrap Icons stylesheet).
    Usage:
        html.Div([html.Span("Title")] + chart_info_icon("my-graph", "..."),
                 className="chart-heading")
    """
    icon_id = f"info-icon-{graph_id}"
    return [
        html.I(id=icon_id, className="bi bi-info-circle-fill chart-info-icon"),
        dbc.Tooltip(tooltip_text, target=icon_id, placement="right"),
    ]


def chart_expand_button(graph_id: str) -> html.Button:
    """
    Small "expand to fullscreen" trigger for a chart card, matching
    new_ga4gh's own image-modal look (see #chart-modal in style.css and
    assets/chart_modal.js). Place it as a sibling of the chart's dcc.Graph
    inside the same html.Figure(...) — assets/chart_modal.js reads the
    caption text from that figure's own <figcaption> at click time, so
    there's no caption string to duplicate here, only the target graph's id.
    """
    return html.Button(
        "⛶",  # ⛶, matches new_ga4gh's plain-glyph close button (×) convention
        className="chart-expand-btn",
        **{
            "data-graph-id": graph_id,
            "aria-label": "Expand chart",
            "title": "Expand chart",
        },
    )


def chart_toolbar(graph_id: str, is_map: bool = False) -> html.Div:
    """
    Permanent icon row [reset (maps only), download PNG, expand to modal],
    replacing Plotly's own modebar. Click handling in assets/chart_toolbar.js
    and assets/chart_modal.js.
    """
    buttons = []
    if is_map:
        buttons.append(
            html.Button(
                html.I(className="bi bi-arrow-counterclockwise"),
                className="chart-reset-btn",
                **{
                    "data-graph-id": graph_id,
                    "aria-label": "Reset map view",
                    "title": "Reset map view",
                },
            )
        )
    buttons.append(
        html.Button(
            html.I(className="bi bi-download"),
            className="chart-download-btn",
            **{
                "data-graph-id": graph_id,
                "aria-label": "Download chart as PNG",
                "title": "Download chart as PNG",
            },
        )
    )
    buttons.append(chart_expand_button(graph_id))
    return html.Div(buttons, className="chart-toolbar")


# ------------------------------------------------------------------
# SHARED AXIS STYLE
# ------------------------------------------------------------------
AXIS_BASE = dict(
    gridcolor=COLORS["grey"],
    linecolor=COLORS["grey"],
    zerolinecolor=COLORS["grey"],
    title_font=dict(size=16),
    automargin=True,          # prevents overlap
    title_standoff=20,        # adds spacing from axis
)

# ------------------------------------------------------------------
# STYLE FUNCTION
# ------------------------------------------------------------------
def apply_ga4gh_styling(fig: go.Figure, height: Optional[int] = 600) -> go.Figure:
    """
    Apply GA4GH styling to any Plotly figure.
    Handles spacing, colors, and trace defaults safely.
    """

    # ------------------------------------------------------------------
    # LAYOUT
    # ------------------------------------------------------------------
    fig.update_layout(
        font=dict(
            family="Figtree-Regular,Figtree,sans-serif",
            size=14,
            color=COLORS["dark"],
        ),
        paper_bgcolor=COLORS["white"],
        plot_bgcolor=COLORS["white"],
        height=height,

        # Increased margins to prevent overlap with tables/labels
        margin=dict(l=80, r=40, t=60, b=80),

        title=dict(x=0.5),

        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=12),
            x=1,
            y=1,
            xanchor="right",
            yanchor="top",
            orientation="v",
        ),

        xaxis=AXIS_BASE,
        yaxis=AXIS_BASE,

        hoverlabel=dict(
            bgcolor=COLORS["white"],
            font_size=14,
            font_family="Figtree, sans-serif",
        ),
    )

    # ------------------------------------------------------------------
    # TRACE STYLING
    # ------------------------------------------------------------------
    for i, trace in enumerate(fig.data):
        default_color = COLORWAY[i % len(COLORWAY)]

        # ---------------- BAR ----------------
        if trace.type == "bar":
            marker = getattr(trace, "marker", None)

            if marker is not None:
                if getattr(marker, "color", None) is None:
                    marker.color = default_color

                if hasattr(marker, "line") and marker.line:
                    marker.line.width = 0

        # ---------------- PIE ----------------
        elif trace.type == "pie":
            n = len(trace.labels) if trace.labels else 0
            marker = getattr(trace, "marker", None)

            if marker is None or getattr(marker, "colors", None) is None:
                trace.marker = dict(
                    colors=COLORWAY[:n],
                    line=dict(color="white", width=2),
                )
            else:
                if hasattr(marker, "line"):
                    marker.line.color = "white"
                    marker.line.width = 2

            if getattr(trace, "pull", None) is None:
                trace.pull = [0.06 if j < 3 else 0 for j in range(n)]

        # ---------------- SCATTER / LINE ----------------
        elif trace.type == "scatter":
            line = getattr(trace, "line", None)

            trace.line = dict(
                width=3,
                color=getattr(line, "color", default_color),
            )
            trace.marker = dict(size=6)

    return fig


# ------------------------------------------------------------------
# OPTIONAL: HELPER FOR TABLE + CHART LAYOUT
# ------------------------------------------------------------------
def apply_table_layout(fig: go.Figure, chart_domain=(0.35, 1.0), table_domain=(0.0, 0.30)):
    """
    Ensures chart and table do not overlap vertically.
    Assumes:
        fig.data[0] = chart
        fig.data[1] = table
    """
    if len(fig.data) >= 2:
        fig.data[0].domain = {"x": [0, 1], "y": list(chart_domain)}
        fig.data[1].domain = {"x": [0, 1], "y": list(table_domain)}

    return fig


# ------------------------------------------------------------------
# GLOBAL TEMPLATE
# ------------------------------------------------------------------
pio.templates["dashboard_theme"] = dict(
    layout=dict(
        # new_ga4gh's body/data font (Figtree Regular) — chart text (axis
        # labels, legends, hover) reads as data, not as a heading.
        font=dict(family="Figtree, sans-serif"),
        margin=dict(l=80, r=40, t=60, b=80),
        xaxis=AXIS_BASE,
        yaxis=AXIS_BASE,
    )
)

pio.templates.default = "dashboard_theme"
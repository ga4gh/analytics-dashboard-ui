# ga4gh_theme.py
from typing import Optional
import plotly.graph_objects as go
import plotly.io as pio

# ------------------------------------------------------------------
# COLORS
# ------------------------------------------------------------------
COLORS = {
    "heroblue": "#02266a",
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
    "lightgrey": "#f4f4f4",
    "grey": "#e8e8e8",
    "border_grey": "#77787b",
    "dark": "#363636",
    "white": "#ffffff",
    "black": "#000000",
}

# ------------------------------------------------------------------
# COLOR SEQUENCE
# ------------------------------------------------------------------
COLORWAY = [
    COLORS["darkblue"],
    COLORS["green"],
    COLORS["red"],
    COLORS["lightblue"],
    COLORS["purple"],
    COLORS["orange"],
    COLORS["secondary_blue"],
    COLORS["pink"],
    COLORS["secondary_orange"],
    COLORS["secondary_purple"],
]

# ------------------------------------------------------------------
# SHARED AXIS STYLE
# ------------------------------------------------------------------
AXIS_BASE = dict(
    gridcolor=COLORS["grey"],
    linecolor=COLORS["border_grey"],
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
            font_family="Work Sans",
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
        font=dict(family="Work Sans, Open Sans, sans-serif"),
        margin=dict(l=80, r=40, t=60, b=80),
        xaxis=AXIS_BASE,
        yaxis=AXIS_BASE,
    )
)

pio.templates.default = "dashboard_theme"
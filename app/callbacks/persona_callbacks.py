from dash import Input, Output, ctx

PERSONA_BUTTONS = [
    "persona-btn-default",
    "persona-btn-funder",
    "persona-btn-researcher",
    "persona-btn-developer",
    "persona-btn-internal",
]

BUTTON_TO_PERSONA = {
    "persona-btn-default":    "default",
    "persona-btn-funder":     "funder",
    "persona-btn-researcher": "researcher",
    "persona-btn-developer":  "developer",
    "persona-btn-internal":   "internal",
}

# ---------------------------------------------------------------------------
# Master registry of every element the persona system controls.
#
# To add a new graph/KPI:
#   1. Add its layout ID to ALL_SECTION_IDS (html.Div) or ALL_COL_IDS (dbc.Col).
#   2. Add that ID to whichever persona(s) should show it in PERSONA_SHOW below.
#      Everything not listed for a persona is hidden automatically.
# ---------------------------------------------------------------------------

# html.Div sections — shown with display:block
ALL_SECTION_IDS = [
    "servicemap",
    "metrics",
    "epmc",
    "github",
    "pypi",
    "tables",
    # shared publication trend chart (funder + researcher)
    "publication-charts",
    # funder-only charts
    "funder-only-charts",
    # researcher-only charts
    "researcher-charts",
]

# dbc.Col KPI cards — shown with {} (let Bootstrap flex handle sizing)
ALL_COL_IDS = [
    # Default KPIs — EPMC-derived; hidden for Developer persona
    "kpi-authors",
    "kpi-citations",
    "kpi-countries",
    # Persona-specific KPIs
    "funder-kpi-yoy",
    "funder-kpi-avg-citations",
    "funder-kpi-funding-bodies",
]

ALL_CONTROLLED_IDS = ALL_SECTION_IDS + ALL_COL_IDS

# ---------------------------------------------------------------------------
# Per-persona whitelist — only list what IS shown.
# Anything omitted is hidden automatically.
# ---------------------------------------------------------------------------
PERSONA_SHOW = {
    "default": {
        "sections": ["servicemap", "metrics", "epmc", "github", "pypi", "tables"],
        "cols":     ["kpi-authors", "kpi-citations", "kpi-countries"],
    },
    "funder": {
        "sections": ["metrics", "epmc", "publication-charts", "funder-only-charts"],
        "cols":     ["kpi-authors", "kpi-citations", "kpi-countries",
                     "funder-kpi-yoy", "funder-kpi-avg-citations", "funder-kpi-funding-bodies"],
    },
    "researcher": {
        "sections": ["metrics", "epmc", "tables", "publication-charts", "researcher-charts"],
        "cols":     ["kpi-authors", "kpi-citations", "kpi-countries",
                     "funder-kpi-yoy", "funder-kpi-avg-citations"],
    },
    "developer": {
        "sections": ["servicemap", "metrics", "github", "pypi"],
        "cols":     [],  # EPMC KPIs hidden — not relevant for developer view
    },
}


def register_persona_callbacks(app):

    # ------------------------------------------------------------------
    # 1. Update the active-persona store when any button is clicked
    # ------------------------------------------------------------------
    @app.callback(
        Output("active-persona", "data"),
        [Input(btn_id, "n_clicks") for btn_id in PERSONA_BUTTONS],
        prevent_initial_call=True,
    )
    def update_active_persona(*_):
        return BUTTON_TO_PERSONA.get(ctx.triggered_id, "default")

    # ------------------------------------------------------------------
    # 2. Highlight the active button; reset all others
    # ------------------------------------------------------------------
    @app.callback(
        [Output(btn_id, "className") for btn_id in PERSONA_BUTTONS]
        + [Output(btn_id, "outline") for btn_id in PERSONA_BUTTONS],
        Input("active-persona", "data"),
    )
    def update_button_styles(active_persona):
        active = active_persona or "default"
        classes = [
            "persona-btn active-persona" if BUTTON_TO_PERSONA[b] == active else "persona-btn"
            for b in PERSONA_BUTTONS
        ]
        outlines = [BUTTON_TO_PERSONA[b] != active for b in PERSONA_BUTTONS]
        return classes + outlines

    # ------------------------------------------------------------------
    # 3. Show / hide sections based on active persona
    # ------------------------------------------------------------------
    @app.callback(
        [Output(eid, "style") for eid in ALL_CONTROLLED_IDS],
        Input("active-persona", "data"),
    )
    def toggle_persona_sections(active_persona):
        persona = active_persona or "default"
        config = PERSONA_SHOW.get(persona, PERSONA_SHOW["default"])
        shown_sections = set(config["sections"])
        shown_cols     = set(config["cols"])
        return [
            {"display": "block"} if eid in shown_sections
            else {}              if eid in shown_cols
            else {"display": "none"}
            for eid in ALL_CONTROLLED_IDS
        ]

from dash import Input, Output, State

# Ids of the geo (non-Mapbox) maps that need zoom/pan clamping — see
# app/assets/map_zoom_clamp.js for why this can't be done via Plotly figure
# config alone. Each has a matching hidden dcc.Store("<id>-zoom-clamp-dummy")
# next to it in its layout, used purely as a callback Output target since
# the clientside function's real work is a Plotly.relayout side effect.
_GEO_MAP_IDS = ["service_map", "epmc-countries-choropleth"]


def register_map_callbacks(app):
    for graph_id in _GEO_MAP_IDS:
        app.clientside_callback(
            "window.dash_clientside.clientside.clampGeoZoom",
            Output(f"{graph_id}-zoom-clamp-dummy", "data"),
            Input(graph_id, "relayoutData"),
            State(graph_id, "id"),
        )

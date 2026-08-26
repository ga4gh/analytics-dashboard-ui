// Plotly's geo subplots (non-Mapbox) have no built-in min/max zoom the way
// Mapbox-based maps do — scroll-zooming out shrinks the map indefinitely
// within its container (leaving background gaps around it), and panning can
// drag the view past the map's own edges/poles. Worse, a zoom-out gesture
// recalculates center toward the cursor position at the same time as scale,
// so clamping scale alone while leaving center wherever it drifted can still
// leave the map off-true (out of frame) even at the "correct" scale. So
// whenever either limit is hit, this snaps the WHOLE view back home — scale
// to 1 (fit-to-container) and center back to (0, 0) — rather than adjusting
// scale/center independently.
window.dash_clientside = window.dash_clientside || {};
window.dash_clientside.clientside = Object.assign({}, window.dash_clientside.clientside, {
    clampGeoZoom: function (relayoutData, graphId) {
        if (!relayoutData) {
            return window.dash_clientside.no_update;
        }

        // The Dash-assigned id lands on the outer .dash-graph wrapper div, not
        // the Plotly-initialized div (.js-plotly-plot) that Plotly.relayout
        // actually needs — it's nested one level inside.
        const wrapper = document.getElementById(graphId);
        const gd = wrapper && wrapper.querySelector(".js-plotly-plot");
        if (!gd || !gd.layout || !gd.layout.geo) {
            return window.dash_clientside.no_update;
        }

        const scale = relayoutData["geo.projection.scale"];
        const lat = relayoutData["geo.center.lat"];

        const scaleExceeded = scale !== undefined && scale <= 1;
        const latExceeded = lat !== undefined && (lat > 85 || lat < -85);

        if (scaleExceeded || latExceeded) {
            Plotly.relayout(gd, {
                "geo.projection.scale": 1,
                "geo.center.lat": 0,
                "geo.center.lon": 0,
            });
        }

        return window.dash_clientside.no_update;
    },
});

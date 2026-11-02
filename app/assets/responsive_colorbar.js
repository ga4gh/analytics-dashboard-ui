// Switches the countries-choropleth colorbar ("Share (%)") between Plotly's
// own vertical/right-side default on desktop and a horizontal bar
// underneath the map on a narrow/touch viewport — colorbar orientation and
// position are Plotly layout properties, not something CSS can touch, so
// this listens for the same (pointer: coarse), (max-width: 768px) condition
// used throughout style.css and calls Plotly.relayout directly instead.
(function () {
    var BREAKPOINT = "(pointer: coarse), (max-width: 768px)";
    var GRAPH_ID = "epmc-countries-choropleth";
    var appliedHorizontal = null; // null = not yet applied, so the first check always runs

    function getPlotlyDiv() {
        var wrapper = document.getElementById(GRAPH_ID);
        if (!wrapper) return null;
        // Dash's id lands on the outer .dash-graph wrapper, not the
        // Plotly-initialized div one level inside — same quirk
        // map_zoom_clamp.js and chart_modal.js work around.
        return wrapper.querySelector(".js-plotly-plot");
    }

    function applyLayout() {
        var gd = getPlotlyDiv();
        if (!gd || !window.Plotly) return;

        var horizontal = window.matchMedia(BREAKPOINT).matches;
        if (horizontal === appliedHorizontal) return; // no change since last check
        appliedHorizontal = horizontal;

        // Switching "coloraxis.colorbar.orientation" via an incremental
        // relayout leaves the PREVIOUS orientation's axis/tick SVG behind
        // (confirmed directly: after flipping to horizontal, a full extra
        // set of vertical tick labels and a phantom axis remained rendered
        // alongside the correct horizontal bar). Toggling showscale off
        // then back on forces Plotly to tear down and fully rebuild the
        // colorbar's SVG instead of patching it in place.
        Plotly.relayout(gd, { "coloraxis.showscale": false }).then(function () {
            if (horizontal) {
                Plotly.relayout(gd, {
                    "coloraxis.showscale": true,
                    "coloraxis.colorbar.orientation": "h",
                    "coloraxis.colorbar.x": 0.5,
                    "coloraxis.colorbar.xanchor": "center",
                    "coloraxis.colorbar.y": -0.2,
                    "coloraxis.colorbar.yanchor": "top",
                    "coloraxis.colorbar.len": 0.9,
                    // Plotly doesn't re-derive title.side when orientation
                    // flips at runtime — it stays "right" (correct for the
                    // vertical bar this figure was built with) and, applied
                    // to a horizontal bar, pushes the "Share (%)" title so
                    // far right it wraps/clips off the card's left edge.
                    // "top" is the correct side for a horizontal colorbar.
                    "coloraxis.colorbar.title.side": "top",
                    "margin.b": 90, // room for the colorbar + its "Share (%)" title below the map
                });
            } else {
                // Plotly's own defaults for a vertical colorbar — explicit
                // here so switching back from mobile is a real reset, not a
                // partial one.
                Plotly.relayout(gd, {
                    "coloraxis.showscale": true,
                    "coloraxis.colorbar.orientation": "v",
                    "coloraxis.colorbar.x": 1.02,
                    "coloraxis.colorbar.xanchor": "left",
                    "coloraxis.colorbar.y": 0.5,
                    "coloraxis.colorbar.yanchor": "middle",
                    "coloraxis.colorbar.len": 1,
                    "coloraxis.colorbar.title.side": "right",
                    "margin.b": 0,
                });
            }
        });
    }

    // The graph may not exist yet on first script execution (Dash mounts
    // components asynchronously) — poll briefly until it does, then also
    // react to live viewport changes (resize, orientation change, DevTools
    // device-toolbar toggling).
    var pollId = setInterval(function () {
        if (getPlotlyDiv()) {
            clearInterval(pollId);
            applyLayout();
        }
    }, 300);

    window.addEventListener("resize", applyLayout);
})();

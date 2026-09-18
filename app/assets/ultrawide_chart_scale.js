// Chart card height is a fixed px value, so past 1920px viewport width the
// fluid grid keeps stretching cards wider without getting taller. Scales
// each card's height by the same factor its width has grown past 1920px.
(function () {
    var BASE_WIDTH = 1920;
    // These already manage their own height (map_mobile_autofit.js,
    // combined_metrics_resize.js, desktop_bar_legend_fix.js) — fighting
    // this script over it flickers.
    var EXCLUDE_IDS = [
        "service_map", "epmc-countries-choropleth",
        "combined-growth-epmc", "combined-citations-over-years",
        "combined-growth-github", "combined-growth-pypi",
        "gh-activity-bar-graph", "gh-interest-graph",
    ];

    var baseHeights = {}; // id -> original px height, captured once

    function tick() {
        var scale = window.innerWidth > BASE_WIDTH ? window.innerWidth / BASE_WIDTH : 1;

        document.querySelectorAll(".js-plotly-plot").forEach(function (gd) {
            var wrapper = gd.parentElement; // Dash-managed wrapper, one level up
            var id = wrapper && wrapper.id;
            if (!id || EXCLUDE_IDS.indexOf(id) !== -1) return;

            if (!(id in baseHeights)) {
                var h = parseFloat(wrapper.style.height);
                baseHeights[id] = !isNaN(h) && h > 0 ? h : null;
            }
            var base = baseHeights[id];
            if (!base || !gd._fullLayout) return;

            var targetHeight = Math.round(base * scale);
            if (Math.abs(gd._fullLayout.height - targetHeight) > 1) {
                wrapper.style.height = targetHeight + "px";
                Plotly.relayout(gd, { height: targetHeight });
            }
        });
    }

    setInterval(tick, 500);
    window.addEventListener("resize", tick);
})();

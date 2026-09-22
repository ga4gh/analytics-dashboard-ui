// On desktop, keeps every pie/donut chart's legend a real 1rem below the
// pie itself, the same way pie_autofit.js already guarantees on mobile.
//
// gh-activity-status-pie, gh-workstream-pie, category-distribution,
// researcher-pub-type-donut, researcher-oa-donut, and funder-region-pie all
// size themselves via a fixed CSS aspect-ratio (chart-aspect-tall/taller)
// so their card scales with viewport width — but the LEGEND's own position
// inside that box is still whatever fraction (legend.y, e.g. -0.1) the
// original desktop figure was tuned with, and as the aspect-ratio-driven
// box scales up on a wide monitor, that fraction can drift away from an
// exact 1rem gap. Unlike the bar-chart version of this same problem
// (desktop_bar_legend_fix.js), the height here isn't changing due to
// autosize chasing a sibling — it's the aspect-ratio's own proportional
// scaling — but the fix is the same: measure the real rendered gap between
// the pie and its legend and nudge margin.b/legend.y by whatever the
// shortfall or excess actually is, rather than trust a single fraction to
// stay correct at every possible card width.
//
// epmc-countries-pie isn't here: its legend is a plain HTML list, not
// Plotly-rendered content (see country_legend_grid.js), so there's nothing
// for this file to measure or correct.
//
// Mobile is untouched: pie_autofit.js already fully owns these same
// charts' sizing AND legend position there (plus a lot more — exact pixel
// height, legend orientation) — running this too would just race that
// script over the same relayout calls.
//
// The actual margin.b/legend.y nudge math is identical to
// desktop_bar_legend_fix.js's own version of this same problem — shared via
// window.__hbarBadgeHelpers.nudgeLegendGap (defined in hbar_mobile_labels.js)
// rather than a second copy of it here. Only the gap *measurement* differs
// (pie-to-legend vs that file's x-axis-to-legend) and stays local to each
// file, since the two chart types have nothing in common to measure against.
(function () {
    var BREAKPOINT = "(pointer: coarse), (max-width: 768px)";
    var CHART_IDS = [
        "gh-activity-status-pie",
        "gh-workstream-pie",
        "category-distribution",
        "researcher-pub-type-donut",
        "researcher-oa-donut",
        "funder-region-pie",
    ];

    function measurePieToLegendGap(gd) {
        var svgs = gd.querySelectorAll("svg.main-svg");
        var pieLayer = svgs[0] && svgs[0].querySelector(".pielayer");
        var legendEl = svgs[1] && svgs[1].querySelector("g.legend");
        if (!pieLayer || !legendEl) return null;
        return legendEl.getBoundingClientRect().top - pieLayer.getBoundingClientRect().bottom;
    }

    function tick() {
        var helpers = window.__hbarBadgeHelpers;
        if (!helpers) return; // hbar_mobile_labels.js hasn't run its top-level code yet
        if (window.matchMedia(BREAKPOINT).matches) return; // pie_autofit.js fully owns mobile

        CHART_IDS.forEach(function (id) {
            var gd = helpers.getPlotlyDiv(id);
            if (!gd || !gd._fullLayout || !gd._fullLayout.legend) return;

            helpers.nudgeLegendGap(gd, measurePieToLegendGap(gd));
        });
    }

    setInterval(tick, 500);
    window.addEventListener("resize", tick);
})();

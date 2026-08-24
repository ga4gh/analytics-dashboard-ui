// On desktop, keeps every legend-bearing bar chart's legend a real 1rem
// below its x-axis labels regardless of how tall its card currently is.
//
// gh-activity-bar-graph, gh-interest-graph, datatable-bar, and
// funder-top-agencies-bar each share a row with a pie/donut chart that
// resizes to fill its card (autosize + config.responsive + a
// chart-aspect-tall/taller CSS ratio) — these 4 were recently given the
// same autosize/responsive treatment so they stretch to match that
// sibling's height instead of staying pinned at a fixed pixel height.
// community-workstream-activity has no pie sibling (it's paired with
// another bar chart) but has the exact same legend-below-x-axis layout and
// benefits from the same continuous correction regardless.
//
// Their own legend.y (e.g. -0.55) is a FRACTION of the plot area's own
// height, tuned back when that plot area was a small, fixed size. Now that
// autosize lets the plot area grow (to match a much taller pie sibling),
// the same fraction produces a far bigger pixel offset than the figure's
// still-fixed margin.b was ever reserving room for — the legend ends up
// positioned way past where the margin actually has space, leaving a big
// visible gap between the x-axis tick labels and wherever the legend lands
// instead of sitting a small, constant distance below them.
//
// Rather than hand-tuning a new fraction for every possible card height
// (fragile — the exact "right" fraction depends on the sibling pie's own
// height, which varies per chart), this measures the REAL rendered gap
// between the x-axis labels and the legend and nudges margin.b/legend.y by
// whatever the shortfall or excess actually is — the same "trust the
// measurement, not the formula" technique already used for these same
// charts' mobile layout (see hbar_mobile_labels.js's own phase-3
// correction), just re-run continuously here since the plot area's height
// can change at any time on desktop (window resize), not just once.
//
// Mobile is untouched: hbar_mobile_labels.js and vbar_to_hbar_mobile.js
// already fully manage these same 4 charts' legend position there (plus a
// lot more — badges, transposition, exact pixel heights) — running this
// too would just race those scripts over the same relayout calls.
(function () {
    var BREAKPOINT = "(pointer: coarse), (max-width: 768px)";
    var CHART_IDS = [
        "gh-activity-bar-graph",
        "gh-interest-graph",
        "datatable-bar",
        "funder-top-agencies-bar",
        "community-workstream-activity",
    ];

    function tick() {
        var helpers = window.__hbarBadgeHelpers;
        if (!helpers) return; // hbar_mobile_labels.js hasn't run its top-level code yet
        if (window.matchMedia(BREAKPOINT).matches) return; // mobile handles these charts itself

        CHART_IDS.forEach(function (id) {
            var gd = helpers.getPlotlyDiv(id);
            if (!gd || !gd._fullLayout || !gd._fullLayout.legend) return;

            var actualGap = helpers.measureAxisToLegendGap(gd);
            if (actualGap === null) return;
            var delta = helpers.GAP - actualGap;
            if (Math.abs(delta) < 1) return;

            var marginT = gd._fullLayout.margin.t;
            var marginB = gd._fullLayout.margin.b;
            var plotAreaHeight = gd._fullLayout.height - marginT - marginB;
            if (plotAreaHeight <= 0) return;

            Plotly.relayout(gd, {
                "margin.b": marginB + delta,
                "legend.yanchor": "top",
                "legend.y": gd._fullLayout.legend.y - delta / plotAreaHeight,
            });
        });
    }

    setInterval(tick, 500);
    window.addEventListener("resize", tick);
})();

// Responsive auto-fit for the app's tall pie/donut charts (GitHub
// activity/workstream, PyPI category, researcher pub-type/OA, funder
// region — NOT the countries pie, which uses a plain HTML legend and a CSS
// aspect-ratio instead, see CHART_IDS below). Desktop is untouched — these
// charts only run at the
// (pointer: coarse), (max-width: 768px) breakpoint used throughout
// style.css, and only ever move things *within* the plot's own layout, not
// the card/title/figcaption around it (that's plain CSS gap, see
// .card-body > figure in style.css).
//
// Why this can't be pure CSS: the legend is Plotly-rendered content inside
// the chart's own SVG, not a separate DOM node — there's nothing for a CSS
// "gap" to apply between the pie and the legend. Getting an exact 1rem gap
// there (and the pie filling the card's full width) means measuring the
// actual rendered pie/legend sizes and computing new margins from them.
(function () {
    var BREAKPOINT = "(pointer: coarse), (max-width: 768px)";
    var CHART_IDS = [
        // epmc-countries-pie isn't here: its legend is now a plain HTML list
        // (see build_countries_legend in epmc_callbacks.py — Plotly's own
        // legend forced a scrollbar for its ~35 entries no matter how much
        // space it got), so the pie itself is just a plain circle sized by
        // .chart-aspect-square in style.css, no legend-margin math needed.
        "gh-activity-status-pie",
        "gh-workstream-pie",
        "category-distribution",
        "researcher-pub-type-donut",
        "researcher-oa-donut",
        "funder-region-pie",
    ];
    var GAP = 16; // 1rem — the pie-to-legend gap this whole file exists to set precisely
    var PLOT_MARGIN = 0; // pie fills the full width Bootstrap's .card-body (1rem native
    // padding) already leaves it — no extra margin on top of that on any side except
    // bottom, which is reserved for the legend below (computed per-chart, see marginB).

    function getPlotlyDiv(id) {
        var wrapper = document.getElementById(id);
        if (!wrapper) return null;
        return wrapper.querySelector(".js-plotly-plot");
    }

    function getPieAndLegend(wrapper) {
        var svgs = wrapper.querySelectorAll("svg.main-svg");
        return {
            pieLayer: svgs[0] && svgs[0].querySelector(".pielayer"),
            legend: svgs[1] && svgs[1].querySelector("g.legend"),
        };
    }

    function measureAndFit(id, onDone) {
        var wrapper = document.getElementById(id);
        var gd = getPlotlyDiv(id);
        if (!wrapper || !gd || !window.Plotly || !gd._fullLayout) return;

        // This element carries no padding of its own — Bootstrap's
        // .card-body already provides a native 1rem inset on every side, so
        // clientWidth here is already the pie's true target width.
        var width = wrapper.clientWidth;
        if (!width) return;

        // Phase 1: render tall with tiny margins so the pie and legend are
        // measured at their true (unclipped, non-scrollable) size — a
        // height that's too short here is exactly what makes Plotly show a
        // scrollable/truncated legend instead of every entry.
        Plotly.relayout(gd, {
            width: width,
            height: 2000,
            margin: { l: PLOT_MARGIN, r: PLOT_MARGIN, t: PLOT_MARGIN, b: PLOT_MARGIN },
            "legend.orientation": "h",
            "legend.xanchor": "center",
            "legend.x": 0.5,
            "legend.yanchor": "top",
            "legend.y": -0.1,
        }).then(function () {
            var parts = getPieAndLegend(wrapper);
            if (!parts.pieLayer || !parts.legend) return;

            var legendHeight = parts.legend.getBoundingClientRect().height;

            var pieDiameter = width;
            var marginB = GAP + legendHeight;
            var figureHeight = PLOT_MARGIN + pieDiameter + marginB;
            wrapper.style.height = figureHeight + "px";

            // legend.y (yanchor:"top") is NOT a fraction of the full figure
            // ("paper") the way it first appears — empirically, y=0 lands
            // the legend's top flush with the PLOT AREA's own bottom edge
            // (not the figure's bottom), and negative y pushes it further
            // below by that fraction of the plot area's OWN height — the
            // same convention this site's desktop figures already rely on
            // via their own y=-0.1. A two-point calibration sampling y=0
            // and y=1 (both still inside/near the plot-area's own span)
            // gave a slope that only held within that span, not out here in
            // the negative/below-plot region — which is exactly why it
            // silently broke for any chart needing a larger negative y
            // relative to its own (smaller) plot area. Solving directly
            // instead: plot area height == pieDiameter (by construction,
            // since margin.t=0 and margin.b is entirely the legend's own
            // reserved space), so y = -GAP / pieDiameter lands the legend
            // exactly GAP px below the pie, no calibration needed.
            var legendY = -GAP / pieDiameter;

            Plotly.relayout(gd, {
                height: figureHeight,
                margin: { l: PLOT_MARGIN, r: PLOT_MARGIN, t: PLOT_MARGIN, b: marginB },
                "legend.orientation": "h",
                "legend.xanchor": "center",
                "legend.x": 0.5,
                "legend.yanchor": "top",
                "legend.y": legendY,
            }).then(function () {
                // The legend can render at a slightly different height once
                // it's actually given its final position/margin than it did
                // during the phase-1 measurement above (seen on the
                // countries pie's 35-item wrapped legend: ~5px shorter) —
                // for most charts the two agree exactly, but when they
                // don't, marginB ends up oversized and leaves slack between
                // the legend and the card's bottom edge instead of a flush
                // GAP-to-figcaption fit. One corrective pass closes that gap
                // by reserving exactly the height the legend actually used.
                var parts2 = getPieAndLegend(wrapper);
                if (!parts2.legend) { if (onDone) onDone(marginB); return; }

                var actualLegendHeight = parts2.legend.getBoundingClientRect().height;
                var delta = legendHeight - actualLegendHeight;

                if (Math.abs(delta) < 1) {
                    if (onDone) onDone(marginB);
                    return;
                }

                var marginB2 = GAP + actualLegendHeight;
                var figureHeight2 = PLOT_MARGIN + pieDiameter + marginB2;
                wrapper.style.height = figureHeight2 + "px";

                Plotly.relayout(gd, {
                    height: figureHeight2,
                    margin: { l: PLOT_MARGIN, r: PLOT_MARGIN, t: PLOT_MARGIN, b: marginB2 },
                    "legend.orientation": "h",
                    "legend.xanchor": "center",
                    "legend.x": 0.5,
                    "legend.yanchor": "top",
                    "legend.y": legendY,
                }).then(function () {
                    if (onDone) onDone(marginB2);
                });
            });
        });
    }

    // Per-chart width this file last fitted at (or "hidden" while its width
    // is 0, or "desktop" once reverted) — NOT just one global mobile/
    // desktop flag. These charts sit behind persona gating (display:none
    // until their persona tab is selected), so a chart can still have
    // clientWidth 0 at the exact moment the rest of the page has already
    // settled into "mobile" — a single one-shot check right then would
    // silently skip it forever, since nothing else ever prompts a re-check
    // once the user later switches to the persona that reveals it.
    var fittedState = {};

    function applyAll() {
        var isMobile = window.matchMedia(BREAKPOINT).matches;

        CHART_IDS.forEach(function (id) {
            var gd = getPlotlyDiv(id);
            if (!gd) return;
            var wrapper = document.getElementById(id);

            if (!isMobile) {
                if (fittedState[id] && fittedState[id] !== "desktop") {
                    // Leaving mobile — hand height/margin/width back to
                    // autosize and Plotly's own template defaults instead of
                    // leaving our computed mobile numbers stuck in place.
                    wrapper.style.height = "";
                    Plotly.relayout(gd, {
                        height: null,
                        width: null,
                        margin: null,
                        "legend.yanchor": "top",
                        "legend.y": -0.1,
                    });
                }
                fittedState[id] = "desktop";
                return;
            }

            var width = wrapper.clientWidth;
            if (!width) {
                // Hidden behind persona gating right now — leave it unfitted
                // so the next tick (persona switch, resize, ...) tries again
                // rather than being silently skipped forever.
                fittedState[id] = null;
                return;
            }

            // Two charts here (gh-workstream-pie, category-distribution)
            // are driven by a Dash callback (Output(..., "figure")) that
            // fires on initial load and can replace the whole figure —
            // margin, legend position, everything — *after* this file has
            // already fitted it once. Checking only clientWidth would miss
            // that entirely (the callback doesn't change the wrapper's own
            // size), so this also re-checks the plot's actual current
            // margin.b against what we last set it to; a mismatch means
            // something else (that callback) rewrote the layout since.
            var current = fittedState[id];
            var marginBNow = gd._fullLayout && gd._fullLayout.margin ? gd._fullLayout.margin.b : null;
            if (current && current.width === width && current.marginB === marginBNow) {
                return; // still exactly as we last left it
            }

            measureAndFit(id, function (marginB) {
                fittedState[id] = { width: width, marginB: marginB };
            });
        });
    }

    // Graphs mount asynchronously, and can also switch between hidden
    // (persona not selected) and visible at any later point the user clicks
    // a persona tab or resizes the window — a recurring check (cheap: just
    // reading clientWidth for 7 elements when nothing's changed) covers all
    // of that instead of a one-shot poll that only ever gets one chance.
    setInterval(applyAll, 500);
    window.addEventListener("resize", applyAll);
})();

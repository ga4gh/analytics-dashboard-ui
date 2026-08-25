// On mobile only, moves the y-axis category labels of horizontal bar charts
// off the axis and onto the bars themselves (grey badge, dark text,
// right-aligned at the plot area's own right edge) — the axis labels' left
// margin was eating into the plot area, leaving the bars themselves
// squeezed into whatever width was left over. Also gives every one of these
// charts the exact same per-row height on mobile, so bar thickness is
// visually consistent across the app regardless of how many rows a given
// chart has, with each badge sized to exactly 2/3 of that row height (a
// visible sliver of the bar's own color still shows above/below it).
// Desktop is untouched: this only ever runs at the (pointer: coarse),
// (max-width: 768px) breakpoint used throughout style.css, and reverts
// cleanly (labels back on the axis, margin/height back to their original
// values) the moment the viewport leaves it.
(function () {
    var BREAKPOINT = "(pointer: coarse), (max-width: 768px)";
    var CHART_IDS = [
        "epmc-authors-bar",
        "funder-top-agencies-bar",
        "dev-repos-by-workstream",
        "dev-standards-service-count",
        "community-workstream-activity",
        "community-top-repos-interest",
    ];

    // Shared with vbar_to_hbar_mobile.js (via window.__hbarBadgeHelpers
    // below) so every mobile bar chart in the app — these 6 already-
    // horizontal ones and the 3 that file transposes from vertical — ends
    // up with the exact same row height and badge proportions, not two
    // separately-tuned numbers drifting apart from each other over time.
    var ROW_HEIGHT_PX = 36;
    // A trivial one-row floor only (not an arbitrary card-height minimum
    // like 400px) — that would inflate row height above ROW_HEIGHT_PX for
    // any chart with few rows (e.g. a 6-row chart would get ~67px rows to
    // fill 400px), defeating the point of one consistent bar thickness.
    var ROW_HEIGHT_MIN_PX = ROW_HEIGHT_PX;
    // Forced explicitly (not left to whatever each chart's own Python
    // figure happens to use) so bar-height-within-a-row is the same
    // fraction everywhere — two charts at the same ROW_HEIGHT_PX could
    // still render different bar thicknesses if their bargaps differed.
    var BARGAP = 0.2;
    // The actual rendered bar thickness every chart is calibrated to hit —
    // NOT derived from ROW_HEIGHT_PX * (1 - BARGAP), because that formula's
    // result depends on how a chart's traces are structured, not just its
    // row count and bargap: gh-activity-bar-graph (20 separate single-bar
    // traces, one per repo) renders visibly thinner bars than a chart with
    // one trace holding 20 category values, at the identical row height and
    // bargap. A fixed target plus a one-shot scale-correction (see phase 2
    // below) is what actually makes every chart's bars match, regardless of
    // *why* their formula-predicted and rendered heights differ.
    var TARGET_BAR_HEIGHT_PX = 24;
    // The annotation "height" property renders larger than the number
    // specified — empirically calibrated (two-point: height:10 -> 17px
    // rendered, height:30 -> 37px rendered, i.e. a flat +7 from this
    // exact borderwidth:1/borderpad:3 combination below) rather than
    // assumed, since Plotly doesn't document the padding/border math.
    var ANNOTATION_HEIGHT_RENDER_OFFSET = 7;
    // TARGET_BAR_HEIGHT_PX is now fixed and known in advance, so the exact
    // final badge height can be computed once, up front, rather than
    // re-derived from a fresh measurement on every single chart.
    var FINAL_BADGE_HEIGHT_PX = Math.max(4, Math.round((TARGET_BAR_HEIGHT_PX * 2) / 3) - ANNOTATION_HEIGHT_RENDER_OFFSET);

    function getPlotlyDiv(id) {
        var wrapper = document.getElementById(id);
        if (!wrapper) return null;
        return wrapper.querySelector(".js-plotly-plot");
    }

    // The category list is each trace's own "y" array rather than reading
    // the axis's computed ticks — a stacked bar (e.g.
    // community-workstream-activity's Active/Moderate/Inactive/Archived
    // segments) has several traces sharing the exact same category set, one
    // segment per category per trace, but all of them still start at x=0.
    function getCategories(gd) {
        var seen = {};
        var categories = [];
        (gd.data || []).forEach(function (trace) {
            (trace.y || []).forEach(function (cat) {
                if (!Object.prototype.hasOwnProperty.call(seen, cat)) {
                    seen[cat] = true;
                    categories.push(cat);
                }
            });
        });
        return categories;
    }

    // Reads the actual rendered height of the first bar's own SVG path —
    // the ground truth for "how tall is a bar right now", since it already
    // reflects this specific chart's current margin.t/margin.b, row count,
    // and bargap rather than a formula that has to guess at all three.
    function measureBarHeight(gd) {
        var path = gd.querySelector(".barlayer .point path");
        return path ? path.getBoundingClientRect().height : null;
    }

    var GAP = 16; // 1rem — same exact-gap technique pie_autofit.js uses for its legends

    // Reads the actual rendered height of the layout legend (color-grouped
    // charts only — datatable-bar's category legend, gh-activity-bar-
    // graph's workstream legend, etc.) — null for the plain single-color
    // charts that have none, so callers can tell "no legend to reserve
    // space for" apart from "legend measured at 0px".
    function measureLegendHeight(gd) {
        var svgs = gd.querySelectorAll("svg.main-svg");
        var legendEl = svgs[1] && svgs[1].querySelector("g.legend");
        if (!legendEl) return null;
        var h = legendEl.getBoundingClientRect().height;
        return h > 0 ? h : null;
    }

    // Unlike the pie/donut charts (no cartesian axis at all), a bar
    // chart's x-axis tick labels (the "0, 200, 400, 600" under the bars)
    // render *below* the plot area, in the same margin.b space the legend
    // needs — reserving only GAP after the plot area, the way pie_autofit.js
    // does for its legends, put the legend right on top of that axis text
    // (confirmed directly: a consistent ~7px overlap across every one of
    // these charts). Measuring the axis's own rendered height and pushing
    // the legend down by that much first is what actually clears it.
    // The x-axis TITLE ("Number of Repositories", "Total Interest", etc.),
    // when present, renders as a separate SVG element (.xtitle) below the
    // tick labels .xaxislayer-above only contains, with its own standoff gap
    // Plotly inserts between the two that isn't documented as a fixed
    // number. Measuring the tick layer's own height and the title's own
    // height separately and adding them together under-counts that standoff
    // (confirmed directly: still clipped "Activity Score" on gh-activity-
    // bar-graph even after doing exactly that) — a single continuous span
    // from the tick layer's top down to the title's bottom captures the
    // ticks, the title, and whatever standoff sits between them all at
    // once, with nothing left to guess at.
    function measureXAxisHeight(gd) {
        var xaxisLayer = gd.querySelector(".xaxislayer-above");
        if (!xaxisLayer) return 0;
        var top = xaxisLayer.getBoundingClientRect().top;
        var titleEl = gd.querySelector(".xtitle");
        var bottom = titleEl ? titleEl.getBoundingClientRect().bottom : xaxisLayer.getBoundingClientRect().bottom;
        return Math.max(0, bottom - top);
    }

    // Ground truth for "is the gap actually GAP px" — reads the real
    // rendered positions rather than trusting the legend.y formula below to
    // have landed exactly where intended. Needed because it doesn't,
    // reliably: measured a consistent 1px shortfall (15px, not 16) on
    // funder-top-agencies-bar and community-workstream-activity even with
    // xAxisHeight already accounted for — the same class of "re-measure and
    // correct" gap pie_autofit.js's own legend needed for one chart earlier
    // this session, not something a single formula reliably nails.
    function measureAxisToLegendGap(gd) {
        var xaxisLayer = gd.querySelector(".xaxislayer-above");
        var svgs = gd.querySelectorAll("svg.main-svg");
        var legendEl = svgs[1] && svgs[1].querySelector("g.legend");
        if (!xaxisLayer || !legendEl) return null;
        // The title (when present) renders below the tick labels, so it —
        // not the tick labels — is the real bottom edge the legend's gap
        // should be measured from; using .xaxislayer-above alone here would
        // count the title's own height as if it were empty gap space.
        var titleEl = gd.querySelector(".xtitle");
        var axisBottom = titleEl ? titleEl.getBoundingClientRect().bottom : xaxisLayer.getBoundingClientRect().bottom;
        return legendEl.getBoundingClientRect().top - axisBottom;
    }

    // Same closed-form pie_autofit.js relies on for its own legends:
    // legend.y (yanchor:"top") is relative to the plot area's own height,
    // not the full figure, so -offset/plotAreaHeight lands the legend's top
    // exactly `offset` px below the plot area's bottom edge, with marginB
    // reserving xAxisHeight (the tick labels bar charts have and pies
    // don't) + GAP (axis-to-legend) + legendHeight + GAP (legend-to-
    // wrapper-bottom, which .card-body > figure's own 1rem figure-gap then
    // carries the rest of the way to the figcaption).
    // Returns null for charts with no legend — the caller then leaves
    // margin.b at whatever this chart's own figure originally used, which
    // is already correct for those (verified: chart-to-caption gap was
    // already exactly 1rem before any of this bar-chart work started).
    function computeLegendCorrection(gd, plotAreaHeight) {
        var legendHeight = measureLegendHeight(gd);
        if (!legendHeight) return null;
        var xAxisHeight = measureXAxisHeight(gd);
        var offset = xAxisHeight + GAP;
        return {
            legendHeight: legendHeight,
            marginB: offset + legendHeight + GAP,
            legendY: -offset / plotAreaHeight,
        };
    }

    function buildAnnotations(categories, badgeHeightPx) {
        return categories.map(function (cat) {
            return {
                // xref "paper" (not "x"/data-space): a fixed position at the
                // plot area's own right edge for every row, rather than each
                // bar's own value — otherwise a short bar would still put
                // its label near the left, not aligned with the others.
                x: 1,
                y: cat,
                xref: "paper",
                yref: "y",
                xanchor: "right",
                yanchor: "middle",
                xshift: -4,
                text: String(cat),
                showarrow: false,
                font: { color: "#363636", size: 10 }, // var(--dark)
                bgcolor: "#efefef", // var(--lightgrey)
                bordercolor: "#767676", // var(--grey)
                borderwidth: 1,
                borderpad: 3,
                // Explicit height (not left to font/borderpad to derive) —
                // that's what makes "2/3 of the bar height" an exact,
                // enforced ratio rather than however tall 10px text with
                // 3px padding happens to render at. Already adjusted by
                // ANNOTATION_HEIGHT_RENDER_OFFSET by the caller — this is
                // the *specified* value, not the true rendered target.
                height: badgeHeightPx,
            };
        });
    }

    // Shared by desktop_bar_legend_fix.js and desktop_pie_legend_fix.js —
    // both poll on an interval, measure their own chart-type-specific gap
    // (x-axis-to-legend for bars, pie-to-legend for pies), and then need
    // this exact same "how far off GAP is that, and how do I nudge
    // margin.b/legend.y to close it" math. The measurement itself can't be
    // shared (different DOM targets per chart type), only this part can.
    function nudgeLegendGap(gd, actualGap) {
        if (actualGap === null) return;
        var delta = GAP - actualGap;
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
    }

    // Exposed for vbar_to_hbar_mobile.js — that file transposes originally-
    // vertical bar charts to horizontal on mobile, then needs this exact
    // same category-extraction + right-aligned-badge-annotation styling and
    // row-height constants, rather than a second, drifting copy of them.
    window.__hbarBadgeHelpers = {
        getPlotlyDiv: getPlotlyDiv,
        getCategories: getCategories,
        measureBarHeight: measureBarHeight,
        computeLegendCorrection: computeLegendCorrection,
        measureAxisToLegendGap: measureAxisToLegendGap,
        nudgeLegendGap: nudgeLegendGap,
        GAP: GAP,
        buildAnnotations: buildAnnotations,
        ROW_HEIGHT_PX: ROW_HEIGHT_PX,
        ROW_HEIGHT_MIN_PX: ROW_HEIGHT_MIN_PX,
        BARGAP: BARGAP,
        TARGET_BAR_HEIGHT_PX: TARGET_BAR_HEIGHT_PX,
        FINAL_BADGE_HEIGHT_PX: FINAL_BADGE_HEIGHT_PX,
    };

    // 16px/1rem on both sides — matches the pie/donut charts' own
    // convention (their margin.l/r are 0, with the 1rem gap coming from
    // .card-body's own native padding instead; these bar charts still need
    // a real Plotly-side margin since the plot area itself, not just the
    // wrapper div, has to stop 1rem short for gridlines/bar edges to line
    // up with the card edge the same way the pie's plot area does).
    var MOBILE_MARGIN_L = 16;
    var MOBILE_MARGIN_R = 16;

    // Every one of these 6 charts renders in Dash's default responsive
    // config, so Plotly resizes to match whatever height the wrapper div
    // itself has — for epmc-authors-bar that's an inline style Python sets
    // per-row already; for the other 5 it's normally nothing at all (they
    // rely on their own figure's fixed layout.height instead). Giving the
    // wrapper an explicit inline height here is what makes ROW_HEIGHT_PX
    // actually take effect for all six uniformly, on top of whichever of
    // those two mechanisms a given chart started with.
    //
    // Sized as plot-area-height (rowCount * ROW_HEIGHT_PX) *plus* this
    // chart's own current margin.t/margin.b, not just rowCount *
    // ROW_HEIGHT_PX alone — two charts at an identical wrapper height can
    // still give their bars different actual thickness if one reserves
    // more top margin for a legend than the other; reserving that margin
    // *on top of* a fixed plot-area budget is what makes bar height
    // actually match across every chart, not just its own row count.
    // Returns the breakdown (not just the total), since phase 2 below needs
    // to scale-correct the plot-area portion specifically without touching
    // margin.t/margin.b again.
    function computeRowHeightPlan(gd) {
        var rowCount = getCategories(gd).length;
        var plotAreaHeight = Math.max(ROW_HEIGHT_MIN_PX, ROW_HEIGHT_PX * rowCount);
        var marginT = gd._fullLayout.margin.t;
        var marginB = gd._fullLayout.margin.b;
        return { plotAreaHeight: plotAreaHeight, marginT: marginT, marginB: marginB, wrapperHeight: plotAreaHeight + marginT + marginB };
    }

    function setWrapperHeight(id, wrapperHeight) {
        var wrapper = document.getElementById(id);
        if (wrapper && parseInt(wrapper.style.height, 10) !== wrapperHeight) {
            wrapper.style.height = wrapperHeight + "px";
        }
    }

    var hadAutomargin = {}; // id -> the yaxis.automargin this chart's own figure was built with
    var originalMarginL = {}; // id -> the margin.l this chart's own figure was built with
    var originalMarginR = {}; // id -> the margin.r this chart's own figure was built with
    var originalYTitle = {}; // id -> the yaxis title text this chart's own figure was built with
    var originalBargap = {}; // id -> the bargap this chart's own figure was built with
    var originalMarginB = {}; // id -> the margin.b this chart's own figure was built with
    var originalHeightPx = {}; // id -> its wrapper's own inline height (often "") before we touched it
    var originalLegendY = {}; // id -> the legend.y this chart's own figure was built with (only if it has a legend)
    var originalLegendYanchor = {}; // id -> the legend.yanchor this chart's own figure was built with
    var lastState = {}; // id -> "mobile" | "desktop", the state last actually applied

    function applyMobile(gd, id) {
        if (!(id in hadAutomargin)) {
            hadAutomargin[id] = !!(gd._fullLayout.yaxis && gd._fullLayout.yaxis.automargin);
            originalMarginL[id] = gd._fullLayout.margin.l;
            originalMarginR[id] = gd._fullLayout.margin.r;
            originalYTitle[id] = (gd._fullLayout.yaxis && gd._fullLayout.yaxis.title && gd._fullLayout.yaxis.title.text) || "";
            originalBargap[id] = gd._fullLayout.bargap;
            originalMarginB[id] = gd._fullLayout.margin.b;
            originalLegendY[id] = gd._fullLayout.legend ? gd._fullLayout.legend.y : undefined;
            originalLegendYanchor[id] = gd._fullLayout.legend ? gd._fullLayout.legend.yanchor : undefined;
            var wrapper = document.getElementById(id);
            if (wrapper) originalHeightPx[id] = wrapper.style.height;
        }
        var plan = computeRowHeightPlan(gd);
        setWrapperHeight(id, plan.wrapperHeight);
        var categories = getCategories(gd);
        // Phase 1: settle the real geometry (an initial guessed plot-area
        // height, forced bargap) with a placeholder badge size — bar height
        // can't be measured correctly until *after* this relayout actually
        // applies. height is set here too, not just as the wrapper's own
        // CSS style above — relying on Plotly's responsive-config
        // ResizeObserver to notice that style change is a *second*,
        // separately-timed async resize this relayout call's own promise
        // does not wait for, so measureBarHeight below could still catch
        // the bar at its pre-resize size. Passing height directly resizes
        // synchronously within the same relayout instead.
        // Returns a promise resolving true only once phase 2 actually
        // measured a real bar and corrected the badge to match — false (not
        // just an unhandled rejection) when the chart was hidden (persona-
        // gated, 0 width) and there was no bar to measure yet, so the caller
        // can tell "applied but not yet correct" apart from "genuinely
        // done" and retry later rather than wrongly treating a placeholder-
        // only result as final.
        return Plotly.relayout(gd, {
            "yaxis.showticklabels": false,
            // automargin:false (not true) — with an explicit margin.l/r set
            // below, leaving automargin on lets Plotly *expand* past that
            // explicit value whenever it decides more room is needed (seen
            // directly: margin.l stayed reported as 16 while the actual
            // rendered gap to the first bar was 42px), which is exactly
            // backwards from what an explicit margin is supposed to
            // guarantee. Nothing needs auto-fitting here anyway — the axis
            // has no tick labels and no title.
            "yaxis.automargin": false,
            "margin.l": MOBILE_MARGIN_L,
            "margin.r": MOBILE_MARGIN_R,
            // Only epmc-authors-bar has a non-empty y title ("Author
            // Name") — with the tick labels it used to sit next to gone,
            // it'd otherwise float alone against the card's left edge.
            "yaxis.title.text": "",
            bargap: BARGAP,
            height: plan.wrapperHeight,
            annotations: buildAnnotations(categories, FINAL_BADGE_HEIGHT_PX),
        }).then(function () {
            // Phase 2: this guessed plot-area height doesn't reliably
            // produce the same rendered bar thickness on every chart (see
            // TARGET_BAR_HEIGHT_PX above) — measure what it actually
            // produced here and scale the plot-area portion (only that
            // part, not the margins already reserved on top of it) by
            // however far off that measurement is from the shared target.
            var barHeight = measureBarHeight(gd);
            if (!barHeight) return false;
            var scale = TARGET_BAR_HEIGHT_PX / barHeight;
            var correctedPlotAreaHeight = Math.round(plan.plotAreaHeight * scale);

            // Only funder-top-agencies-bar and community-workstream-
            // activity (of these 6) have a color-grouped legend — the
            // other 4's chart-to-caption gap is already exactly 1rem via
            // .card-body > figure's own gap, unrelated to any of this.
            var legendCorrection = computeLegendCorrection(gd, correctedPlotAreaHeight);
            var marginB = legendCorrection ? legendCorrection.marginB : plan.marginB;
            var correctedWrapperHeight = correctedPlotAreaHeight + plan.marginT + marginB;
            setWrapperHeight(id, correctedWrapperHeight);

            var relayoutProps = { height: correctedWrapperHeight };
            if (legendCorrection) {
                relayoutProps["margin.b"] = marginB;
                relayoutProps["legend.yanchor"] = "top";
                relayoutProps["legend.y"] = legendCorrection.legendY;
            }
            return Plotly.relayout(gd, relayoutProps).then(function () {
                if (!legendCorrection) return true;
                // Phase 3: the formula above doesn't reliably land the gap
                // exactly (measured a consistent 1px shortfall on both
                // funder-top-agencies-bar and community-workstream-activity
                // even with xAxisHeight already accounted for) — measure
                // the real rendered gap and nudge marginB/legend.y by
                // whatever the shortfall/excess actually is, the same
                // "trust the measurement, not the formula" correction
                // pie_autofit.js needed for its own legend earlier.
                var actualGap = measureAxisToLegendGap(gd);
                if (actualGap === null) return true;
                var delta = GAP - actualGap;
                if (Math.abs(delta) < 0.5) return true;
                var fixedMarginB = marginB + delta;
                var fixedLegendY = legendCorrection.legendY - delta / correctedPlotAreaHeight;
                var fixedWrapperHeight = correctedWrapperHeight + delta;
                setWrapperHeight(id, fixedWrapperHeight);
                return Plotly.relayout(gd, {
                    height: fixedWrapperHeight,
                    "margin.b": fixedMarginB,
                    "legend.y": fixedLegendY,
                }).then(function () {
                    return true;
                });
            });
        });
    }

    function applyDesktop(gd, id) {
        var wrapper = document.getElementById(id);
        if (wrapper && id in originalHeightPx) wrapper.style.height = originalHeightPx[id];
        Plotly.relayout(gd, {
            "yaxis.showticklabels": true,
            "yaxis.automargin": hadAutomargin[id],
            "margin.l": hadAutomargin[id] ? null : originalMarginL[id],
            "margin.r": originalMarginR[id],
            "margin.b": originalMarginB[id],
            "legend.y": originalLegendY[id],
            "legend.yanchor": originalLegendYanchor[id],
            "yaxis.title.text": originalYTitle[id],
            bargap: originalBargap[id],
            annotations: [],
        });
    }

    var lastSignature = {}; // id -> "rowCount:marginT:marginB" last actually applied

    function tick() {
        var isMobile = window.matchMedia(BREAKPOINT).matches;
        CHART_IDS.forEach(function (id) {
            var gd = getPlotlyDiv(id);
            if (!gd || !gd._fullLayout) return;

            if (isMobile) {
                // Every one of these 6 charts is (re)built by a Dash
                // callback that fires after initial mount, and a top-n
                // slider can rebuild it again at any later point — a plain
                // one-shot "already handled" flag would catch the empty
                // placeholder figure on the first tick or two and then
                // never notice a real rebuild resetting showticklabels/row
                // count/bargap/badge sizing. Comparing a cheap signature
                // (not re-running the full 2-phase relayout unconditionally
                // every 500ms) catches that while staying idempotent once
                // stable.
                var showingAxisLabels = !gd._fullLayout.yaxis || gd._fullLayout.yaxis.showticklabels !== false;
                // margin.t only, not margin.b — funder-top-agencies-bar and
                // community-workstream-activity's own phase 2 now sets
                // margin.b itself (reserving exact legend space), so
                // including it here would make the signature never
                // stabilize: it'd differ from lastSignature on every tick
                // (checked against the pre-correction value) forever, even
                // once the chart is genuinely already correct.
                var signature = getCategories(gd).length + ":" + gd._fullLayout.margin.t;
                if (showingAxisLabels || lastState[id] !== "mobile" || lastSignature[id] !== signature) {
                    lastState[id] = "mobile";
                    // lastSignature is set only once applyMobile's own
                    // promise confirms phase 2 actually measured a real bar
                    // (see there) — while it's still unset/stale, every
                    // subsequent tick's signature check above keeps
                    // retrying instead of wrongly treating a
                    // hidden-chart, placeholder-only result as finished.
                    applyMobile(gd, id).then(function (succeeded) {
                        if (succeeded) lastSignature[id] = signature;
                    });
                }
            } else if (lastState[id] === "mobile") {
                applyDesktop(gd, id);
                lastState[id] = "desktop";
                delete lastSignature[id];
            }
        });
    }

    // Persona-gated charts (funder/developer/community sections) sit behind
    // display:none until their tab is picked, so a recurring check (not a
    // one-shot poll) is needed to catch them once they become visible —
    // same reasoning as pie_autofit.js.
    setInterval(tick, 500);
    window.addEventListener("resize", tick);
})();

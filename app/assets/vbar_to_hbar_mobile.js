// On mobile only, transposes these originally-VERTICAL bar charts (long
// project/repo names crowded along the x-axis, already at -45deg and still
// overlapping past ~20 bars) into horizontal ones, then applies the exact
// same treatment already used for the app's other horizontal bar charts:
// category labels off the axis, overlaid as right-aligned grey badges, via
// hbar_mobile_labels.js's shared helpers (window.__hbarBadgeHelpers).
// Desktop is untouched — reverts to the original vertical orientation,
// axis titles, margins, and height the moment the viewport leaves the
// (pointer: coarse), (max-width: 768px) breakpoint used throughout style.css.
(function () {
    var BREAKPOINT = "(pointer: coarse), (max-width: 768px)";
    var CHART_IDS = ["datatable-bar", "gh-activity-bar-graph", "gh-interest-graph"];
    // 16px/1rem on both sides — matches hbar_mobile_labels.js's own already-
    // horizontal charts and the pie/donut charts' 1rem card-edge gap.
    var MOBILE_MARGIN_L = 16;
    var MOBILE_MARGIN_R = 16;
    var MOBILE_MARGIN_B = 40; // was 300, reserved for the now-removed rotated x-axis category labels

    function getPlotlyDiv(id) {
        var wrapper = document.getElementById(id);
        if (!wrapper) return null;
        return wrapper.querySelector(".js-plotly-plot");
    }

    // Plotly encodes numeric trace arrays as a compact {dtype, bdata}
    // object (base64), not a plain JS array — handing that same object
    // straight back to Plotly.restyle as the value for a *different*
    // property (x <- old y) silently no-ops instead of erroring: orientation
    // (a plain string) in the same restyle call still applies, x/y just
    // quietly stay put. Decoding to a plain array first avoids that.
    var TYPED_ARRAY_CTORS = {
        f8: Float64Array, f4: Float32Array,
        i1: Int8Array, i2: Int16Array, i4: Int32Array,
        u1: Uint8Array, u2: Uint16Array, u4: Uint32Array,
    };

    function decodeMaybeBdata(value) {
        if (!value || typeof value !== "object" || Array.isArray(value) || !value.bdata) {
            return value; // already a plain array (or something else entirely)
        }
        var binary = atob(value.bdata);
        var bytes = new Uint8Array(binary.length);
        for (var i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
        var TypedCtor = TYPED_ARRAY_CTORS[value.dtype] || Float64Array;
        return Array.prototype.slice.call(new TypedCtor(bytes.buffer));
    }

    var original = {}; // id -> snapshot of everything transposeToHorizontal changes
    var lastState = {}; // id -> "mobile" | "desktop", the state last actually applied

    // Snapshots the trace x/y/orientation arrays and axis/margin/height
    // config *before* transposing — called fresh every time the chart is
    // seen still vertical, not just once ever, since a slider-driven Dash
    // callback (top-n, gh-top-n) can rebuild the whole figure back to
    // vertical with entirely new data at any time while already on mobile.
    function captureOriginal(gd, id) {
        var wrapper = document.getElementById(id);
        var prev = original[id];
        // A fresh capture runs whenever isActuallyTransposed() reports
        // false, including the not-fully-root-caused case (see there) where
        // some external re-render leaves orientation/data reverted but
        // doesn't actually hand back a genuine fresh vertical figure — at
        // that exact moment gd._fullLayout.yaxis.title.text can still read
        // back as "" (this same code's own earlier mobile pass, not the
        // real Python-authored title), permanently wiping a real title like
        // "Activity Score" the next time transposeToHorizontal runs.
        // Falling back to the previous capture whenever the fresh read is
        // empty means an accidental blank reading can never clobber a title
        // this code already knows is real.
        var freshXTitle = (gd._fullLayout.xaxis.title && gd._fullLayout.xaxis.title.text) || "";
        var freshYTitle = (gd._fullLayout.yaxis.title && gd._fullLayout.yaxis.title.text) || "";
        original[id] = {
            traceX: gd.data.map(function (t) { return decodeMaybeBdata(t.x); }),
            traceY: gd.data.map(function (t) { return decodeMaybeBdata(t.y); }),
            traceOrientation: gd.data.map(function (t) { return t.orientation || "v"; }),
            xaxisTitle: freshXTitle || (prev ? prev.xaxisTitle : ""),
            yaxisTitle: freshYTitle || (prev ? prev.yaxisTitle : ""),
            xaxisShowgrid: !!gd._fullLayout.xaxis.showgrid,
            yaxisShowgrid: !!gd._fullLayout.yaxis.showgrid,
            marginL: gd._fullLayout.margin.l,
            marginR: gd._fullLayout.margin.r,
            marginB: gd._fullLayout.margin.b,
            bargap: gd._fullLayout.bargap,
            legendY: gd._fullLayout.legend ? gd._fullLayout.legend.y : undefined,
            legendYanchor: gd._fullLayout.legend ? gd._fullLayout.legend.yanchor : undefined,
            wrapperHeightStyle: wrapper ? wrapper.style.height : "",
        };
    }

    function transposeToHorizontal(gd, id) {
        var orig = original[id];
        var indices = gd.data.map(function (_, i) { return i; });
        Plotly.restyle(
            gd,
            {
                x: orig.traceY,
                y: orig.traceX,
                orientation: indices.map(function () { return "h"; }),
            },
            indices
        );

        Plotly.relayout(gd, {
            // The old category x-axis's own tickangle/automargin (set for
            // -45deg rotated long labels) would otherwise apply to the new,
            // numeric x-axis instead — this axis is the value axis now.
            "xaxis.tickangle": 0,
            "xaxis.automargin": false,
            "xaxis.title.text": orig.yaxisTitle,
            "xaxis.showgrid": orig.yaxisShowgrid,
            "yaxis.title.text": "",
            "yaxis.showgrid": false,
            "yaxis.showticklabels": false,
            // automargin:false (not true) — with an explicit margin.l/r set
            // below, leaving automargin on lets Plotly expand past that
            // explicit value whenever it decides more room is needed (see
            // hbar_mobile_labels.js's own version of this same fix), which
            // is backwards from what an explicit margin should guarantee.
            "yaxis.automargin": false,
            "margin.l": MOBILE_MARGIN_L,
            "margin.r": MOBILE_MARGIN_R,
            "margin.b": MOBILE_MARGIN_B,
        });
    }

    function restoreVertical(gd, id) {
        var orig = original[id];
        var indices = gd.data.map(function (_, i) { return i; });
        Plotly.restyle(
            gd,
            { x: orig.traceX, y: orig.traceY, orientation: orig.traceOrientation },
            indices
        );

        Plotly.relayout(gd, {
            "xaxis.tickangle": -45,
            "xaxis.automargin": true,
            "xaxis.title.text": orig.xaxisTitle,
            "xaxis.showgrid": orig.xaxisShowgrid,
            "yaxis.title.text": orig.yaxisTitle,
            "yaxis.showgrid": orig.yaxisShowgrid,
            "yaxis.showticklabels": true,
            "yaxis.automargin": false,
            "margin.l": orig.marginL,
            "margin.r": orig.marginR,
            "margin.b": orig.marginB,
            "legend.y": orig.legendY,
            "legend.yanchor": orig.legendYanchor,
            bargap: orig.bargap,
            annotations: [],
        });

        var wrapper = document.getElementById(id);
        if (wrapper) wrapper.style.height = orig.wrapperHeightStyle;
    }

    function applyLabelsAndHeight(gd, id) {
        var helpers = window.__hbarBadgeHelpers;
        var categories = helpers.getCategories(gd);

        // Same ROW_HEIGHT_PX as hbar_mobile_labels.js's own already-
        // horizontal charts — one consistent bar thickness across every
        // mobile bar chart in the app. Reserves plot-area height
        // (rowCount * ROW_HEIGHT_PX) *plus* this chart's own current
        // margin.t/margin.b on top, not just rowCount * ROW_HEIGHT_PX alone
        // — gh-interest-graph's margin.t (80, for its legend) is 4x
        // gh-activity-bar-graph's (20), so without adding it back on top,
        // gh-interest-graph's bars would render thinner than the others at
        // the same wrapper height even with an identical row count.
        var wrapper = document.getElementById(id);
        var plotAreaHeight = Math.max(helpers.ROW_HEIGHT_MIN_PX, helpers.ROW_HEIGHT_PX * categories.length);
        var marginT = gd._fullLayout.margin.t;
        var marginB = gd._fullLayout.margin.b;
        var guessedWrapperHeight = plotAreaHeight + marginT + marginB;
        if (wrapper && parseInt(wrapper.style.height, 10) !== guessedWrapperHeight) {
            wrapper.style.height = guessedWrapperHeight + "px";
        }

        // Phase 1: settle bargap with a placeholder badge size — bar height
        // can't be measured correctly until *after* this relayout applies.
        // height is set here too (not just the wrapper's own CSS style
        // above) so Plotly resizes synchronously within this same relayout
        // instead of via a separately-timed ResizeObserver pass that
        // phase 2's bar measurement below could otherwise race against.
        Plotly.relayout(gd, {
            bargap: helpers.BARGAP,
            height: guessedWrapperHeight,
            annotations: helpers.buildAnnotations(categories, helpers.FINAL_BADGE_HEIGHT_PX),
        }).then(function () {
            // Phase 2: this guessed plot-area height doesn't reliably
            // produce the same rendered bar thickness on every chart (e.g.
            // gh-activity-bar-graph's 20 separate single-bar traces render
            // visibly thinner bars than a chart with one trace holding 20
            // category values, at an identical row height/bargap) — measure
            // what it actually produced and scale the plot-area portion
            // (only that part, not the margins already reserved on top of
            // it) by however far off that measurement is from the shared
            // target every chart is calibrated to hit.
            var barHeight = helpers.measureBarHeight(gd);
            if (!barHeight) return;
            var scale = helpers.TARGET_BAR_HEIGHT_PX / barHeight;
            var correctedPlotAreaHeight = Math.round(plotAreaHeight * scale);

            // All 3 of these charts have a color-grouped legend (category/
            // workstream/metric) — reserve exactly 1rem before and after it
            // instead of the placeholder MOBILE_MARGIN_B, the same
            // plot-area-relative legend.y closed form pie_autofit.js uses
            // for its own legends (see hbar_mobile_labels.js's
            // computeLegendCorrection for the full reasoning).
            var legendCorrection = helpers.computeLegendCorrection(gd, correctedPlotAreaHeight);
            var correctedMarginB = legendCorrection ? legendCorrection.marginB : marginB;
            var correctedWrapperHeight = correctedPlotAreaHeight + marginT + correctedMarginB;
            if (wrapper) wrapper.style.height = correctedWrapperHeight + "px";

            var relayoutProps = { height: correctedWrapperHeight };
            if (legendCorrection) {
                relayoutProps["margin.b"] = correctedMarginB;
                relayoutProps["legend.yanchor"] = "top";
                relayoutProps["legend.y"] = legendCorrection.legendY;
            }
            return Plotly.relayout(gd, relayoutProps).then(function () {
                if (!legendCorrection) return;
                // Phase 3: the formula above doesn't reliably land the gap
                // exactly (see hbar_mobile_labels.js's own version of this
                // same correction) — measure the real rendered gap and
                // nudge marginB/legend.y by whatever the shortfall/excess
                // actually is.
                var actualGap = helpers.measureAxisToLegendGap(gd);
                if (actualGap === null) return;
                var delta = helpers.GAP - actualGap;
                if (Math.abs(delta) < 0.5) return;
                var fixedMarginB = correctedMarginB + delta;
                var fixedLegendY = legendCorrection.legendY - delta / correctedPlotAreaHeight;
                var fixedWrapperHeight = correctedWrapperHeight + delta;
                if (wrapper) wrapper.style.height = fixedWrapperHeight + "px";
                return Plotly.relayout(gd, {
                    height: fixedWrapperHeight,
                    "margin.b": fixedMarginB,
                    "legend.y": fixedLegendY,
                });
            });
        });
    }

    // orientation alone isn't a reliable enough signal that the transpose
    // actually stuck — reproduced directly: some external re-render (still
    // not fully root-caused) can leave orientation:"h" while x/y quietly
    // revert to their original (pre-swap) values, and that combination
    // holds stable indefinitely once it happens, not just for one tick.
    // Checking x[0]'s actual type catches that regardless of why it
    // happened: the value axis must be numeric, never the category text.
    function isActuallyTransposed(gd) {
        if (gd.data[0].orientation !== "h") return false;
        var x0 = gd.data[0].x;
        var firstVal = Array.isArray(x0) ? x0[0] : x0;
        return typeof firstVal === "number";
    }

    function tick() {
        if (!window.__hbarBadgeHelpers) return; // hbar_mobile_labels.js hasn't run its top-level code yet
        var isMobile = window.matchMedia(BREAKPOINT).matches;

        CHART_IDS.forEach(function (id) {
            var gd = getPlotlyDiv(id);
            if (!gd || !gd._fullLayout || !gd.data || !gd.data.length) return;

            var transposed = isActuallyTransposed(gd);

            if (isMobile) {
                if (!transposed) {
                    // Either the first time this chart's been seen, a
                    // slider-driven callback just rebuilt it back to
                    // vertical with fresh data, or the swap silently didn't
                    // stick last time — capture *this* data and (re)transpose.
                    captureOriginal(gd, id);
                    transposeToHorizontal(gd, id);
                }
                applyLabelsAndHeight(gd, id);
                lastState[id] = "mobile";
            } else if (lastState[id] === "mobile" && gd.data[0].orientation === "h") {
                restoreVertical(gd, id);
                lastState[id] = "desktop";
            }
        });
    }

    setInterval(tick, 500);
    window.addEventListener("resize", tick);
})();

// On mobile only, shrinks the service_map geo card down to the height its
// actual rendered map content needs, instead of the fixed desktop-era 700px
// that leaves a huge blank gap above and below the map on a much narrower
// mobile card — the "natural earth" projection keeps its own geographic
// aspect ratio regardless of the box it's given, so a box far taller than
// a ~309px-wide world map actually needs (measured: ~160px) just renders
// as dead space, not a bigger map.
//
// epmc-countries-choropleth is included too. It was originally left out: at
// any total figure height below ~650px the geo would degrade to a fraction
// of its natural width no matter what. That turned out to be a side effect
// of a since-fixed bug in responsive_colorbar.js, where switching the
// colorbar to horizontal via an incremental relayout left the old vertical
// colorbar's axis/ticks rendered underneath it — Plotly's automargin logic
// was reserving height for that phantom vertical axis and stealing it from
// the geo whenever the total height was reduced. Now that the colorbar
// relayout does a full teardown/rebuild instead of patching in place, the
// height competition is gone and this chart fits the same way service_map
// does.
//
// Desktop is untouched: this only ever runs at the (pointer: coarse),
// (max-width: 768px) breakpoint used throughout style.css, and reverts to
// the original fixed height the moment the viewport leaves it.
(function () {
    var BREAKPOINT = "(pointer: coarse), (max-width: 768px)";
    var CHART_IDS = ["service_map", "epmc-countries-choropleth"];

    function getPlotlyDiv(id) {
        var wrapper = document.getElementById(id);
        if (!wrapper) return null;
        return wrapper.querySelector(".js-plotly-plot");
    }

    function measureGeoHeight(gd) {
        var geoLayer = gd.querySelector(".geolayer");
        var h = geoLayer ? geoLayer.getBoundingClientRect().height : null;
        return h > 0 ? h : null;
    }

    var original = {}; // id -> { height, wrapperHeightStyle } before we touched it
    var lastState = {}; // id -> "mobile" | "desktop"
    var lastFitSignature = {}; // id -> "width:marginB" this chart was last successfully fit against

    function captureOriginal(gd, id) {
        var wrapper = document.getElementById(id);
        original[id] = {
            height: gd._fullLayout.height,
            wrapperHeightStyle: wrapper ? wrapper.style.height : "",
        };
    }

    function applyMobile(gd, id) {
        if (!(id in original)) captureOriginal(gd, id);
        var wrapper = document.getElementById(id);
        if (!wrapper) return Promise.resolve(null);
        var width = wrapper.clientWidth;
        if (!width) return Promise.resolve(null); // hidden (persona-gated), try again next tick

        // Phase 1: render tall so the map's own natural rendered height at
        // this width can be measured unclipped.
        return Plotly.relayout(gd, { width: width, height: 900 }).then(function () {
            var geoHeight = measureGeoHeight(gd);
            if (!geoHeight) return null;
            var marginT = gd._fullLayout.margin.t;
            var marginB = gd._fullLayout.margin.b;
            var targetHeight = Math.ceil(geoHeight) + marginT + marginB;
            wrapper.style.height = targetHeight + "px";
            // Phase 2: height passed directly here (not left to a separate
            // ResizeObserver reacting to the style change above), so this
            // relayout's own promise reflects the final settled size.
            return Plotly.relayout(gd, { height: targetHeight }).then(function () {
                return width + ":" + marginB;
            });
        });
    }

    function applyDesktop(gd, id) {
        var orig = original[id];
        if (!orig) return;
        var wrapper = document.getElementById(id);
        if (wrapper) wrapper.style.height = orig.wrapperHeightStyle;
        Plotly.relayout(gd, { height: orig.height, width: null });
    }

    function tick() {
        var isMobile = window.matchMedia(BREAKPOINT).matches;
        CHART_IDS.forEach(function (id) {
            var gd = getPlotlyDiv(id);
            if (!gd || !gd._fullLayout) return;

            if (isMobile) {
                var wrapper = document.getElementById(id);
                var width = wrapper ? wrapper.clientWidth : 0;
                var signature = width + ":" + gd._fullLayout.margin.b;
                // Re-fit whenever not yet fit at all, or the signature
                // (card width, or epmc-countries-choropleth's margin.b once
                // responsive_colorbar.js's own separate poll changes it)
                // has drifted from what was last actually fit against —
                // idempotent once genuinely stable, since a successful fit
                // stores the exact signature it measured, not just "mobile".
                if (lastState[id] !== "mobile" || lastFitSignature[id] !== signature) {
                    lastState[id] = "mobile";
                    applyMobile(gd, id).then(function (fitSignature) {
                        if (fitSignature) lastFitSignature[id] = fitSignature;
                    });
                }
            } else if (lastState[id] === "mobile") {
                applyDesktop(gd, id);
                lastState[id] = "desktop";
                delete lastFitSignature[id];
            }
        });
    }

    setInterval(tick, 500);
    window.addEventListener("resize", tick);
})();

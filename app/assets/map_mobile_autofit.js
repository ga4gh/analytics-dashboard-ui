// Fits these geo cards' height to their actual rendered map content at any
// width — "natural earth" keeps its own aspect ratio, so a fixed height
// leaves dead space (or squeezes the map) at the wrong width.
(function () {
    var BREAKPOINT = "(pointer: coarse), (max-width: 768px)";
    var ALWAYS_FIT_IDS = ["service_map", "epmc-countries-choropleth"];
    var MOBILE_ONLY_IDS = [];
    var CHART_IDS = ALWAYS_FIT_IDS.concat(MOBILE_ONLY_IDS);

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

    function applyFit(gd, id) {
        if (!(id in original)) captureOriginal(gd, id);
        var wrapper = document.getElementById(id);
        if (!wrapper) return Promise.resolve(null);
        var width = wrapper.clientWidth;
        if (!width) return Promise.resolve(null); // hidden (persona-gated), try again next tick

        // Re-measure after each candidate height in case margins (e.g. a
        // colorbar's automargin) haven't settled after just one relayout.
        function settle(prevGeoHeight, iterationsLeft) {
            var geoHeight = measureGeoHeight(gd);
            if (!geoHeight) return Promise.resolve(null);
            if (iterationsLeft <= 0 || (prevGeoHeight !== null && Math.abs(geoHeight - prevGeoHeight) < 1)) {
                return Promise.resolve(width + ":" + gd._fullLayout.margin.b);
            }
            var marginT = gd._fullLayout.margin.t;
            var marginB = gd._fullLayout.margin.b;
            var targetHeight = Math.ceil(geoHeight) + marginT + marginB;
            wrapper.style.height = targetHeight + "px";
            return Plotly.relayout(gd, { height: targetHeight, width: width }).then(function () {
                return settle(geoHeight, iterationsLeft - 1);
            });
        }

        // Render tall first so the map's natural height at this width can
        // be measured unclipped.
        return Plotly.relayout(gd, { width: width, height: 900 }).then(function () {
            return settle(null, 4);
        });
    }

    function applyUnfit(gd, id) {
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

            var shouldFit = isMobile || ALWAYS_FIT_IDS.indexOf(id) !== -1;

            if (shouldFit) {
                var wrapper = document.getElementById(id);
                var width = wrapper ? wrapper.clientWidth : 0;
                var signature = width + ":" + gd._fullLayout.margin.b;
                if (lastState[id] !== "fitted" || lastFitSignature[id] !== signature) {
                    lastState[id] = "fitted";
                    applyFit(gd, id).then(function (fitSignature) {
                        if (fitSignature) lastFitSignature[id] = fitSignature;
                    });
                }
            } else if (lastState[id] === "fitted") {
                applyUnfit(gd, id);
                lastState[id] = "unfitted";
                delete lastFitSignature[id];
            }
        });
    }

    setInterval(tick, 500);
    window.addEventListener("resize", tick);
})();

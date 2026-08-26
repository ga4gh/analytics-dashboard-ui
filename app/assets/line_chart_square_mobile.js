// On mobile only, makes the "Cumulative Metrics" line charts square (1:1)
// instead of each rendering at its desktop-era fixed 430px height
// regardless of how narrow the stacked mobile card actually is — matches
// the width the card currently has, the same "measure and match" approach
// map_mobile_autofit.js uses for the map cards.
// Desktop is untouched: this only ever runs at the (pointer: coarse),
// (max-width: 768px) breakpoint used throughout style.css, and reverts to
// the original fixed height the moment the viewport leaves it.
(function () {
    var BREAKPOINT = "(pointer: coarse), (max-width: 768px)";
    var CHART_IDS = [
        "combined-growth-epmc",
        "combined-citations-over-years",
        "combined-growth-github",
        "combined-growth-pypi",
    ];

    function getPlotlyDiv(id) {
        var wrapper = document.getElementById(id);
        if (!wrapper) return null;
        return wrapper.querySelector(".js-plotly-plot");
    }

    var original = {}; // id -> { height, wrapperHeightStyle } before we touched it
    var lastState = {}; // id -> "mobile" | "desktop"
    var lastFitWidth = {}; // id -> the width this chart was last squared against

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
        if (!wrapper) return;
        var width = wrapper.clientWidth;
        if (!width) return; // hidden or not yet laid out, try again next tick

        // height passed directly in the same relayout call (not left to a
        // separately-timed ResizeObserver reacting to the style change
        // alone) so the square is exact as soon as this call resolves.
        wrapper.style.height = width + "px";
        Plotly.relayout(gd, { height: width });
        lastFitWidth[id] = width;
    }

    function applyDesktop(gd, id) {
        var orig = original[id];
        if (!orig) return;
        var wrapper = document.getElementById(id);
        if (wrapper) wrapper.style.height = orig.wrapperHeightStyle;
        Plotly.relayout(gd, { height: orig.height });
    }

    function tick() {
        var isMobile = window.matchMedia(BREAKPOINT).matches;
        CHART_IDS.forEach(function (id) {
            var gd = getPlotlyDiv(id);
            if (!gd || !gd._fullLayout) return;

            if (isMobile) {
                var wrapper = document.getElementById(id);
                var width = wrapper ? wrapper.clientWidth : 0;
                // Re-square whenever not yet squared, or the card's own
                // width has changed (orientation change, sidebar toggle,
                // window resize) since the last time this was applied.
                if (lastState[id] !== "mobile" || lastFitWidth[id] !== width) {
                    lastState[id] = "mobile";
                    applyMobile(gd, id);
                }
            } else if (lastState[id] === "mobile") {
                applyDesktop(gd, id);
                lastState[id] = "desktop";
                delete lastFitWidth[id];
            }
        });
    }

    setInterval(tick, 500);
    window.addEventListener("resize", tick);
})();

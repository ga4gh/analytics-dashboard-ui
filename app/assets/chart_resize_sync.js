// config.responsive alone doesn't reliably keep every chart's own Plotly
// figure in sync with its actual container size on desktop — confirmed
// charts staying at an old width/height (overlapping neighbouring cards)
// after a window resize, or after a sibling's height changed for some other
// reason (e.g. a taller pie in the same row). This continuously measures
// each chart's wrapper and relayouts to match whenever they drift apart.
// Desktop only — mobile's viewport/window size doesn't change in practice,
// and several charts there are already individually managed by
// hbar_mobile_labels.js / vbar_to_hbar_mobile.js.
(function () {
    var BREAKPOINT = "(pointer: coarse), (max-width: 768px)";
    // These already manage their own width/height on desktop.
    var EXCLUDE_IDS = [
        "service_map", "epmc-countries-choropleth",
        "combined-growth-epmc", "combined-citations-over-years",
        "combined-growth-github", "combined-growth-pypi",
    ];

    function tick() {
        if (window.matchMedia(BREAKPOINT).matches) return;

        document.querySelectorAll(".js-plotly-plot").forEach(function (gd) {
            var wrapper = gd.parentElement;
            var id = wrapper && wrapper.id;
            if (!id || EXCLUDE_IDS.indexOf(id) !== -1 || !gd._fullLayout) return;

            var targetWidth = wrapper.clientWidth;
            var targetHeight = wrapper.clientHeight;
            if (!targetWidth || !targetHeight) return;

            // >3px (not >1) tolerance — Plotly's own automargin can shift a
            // couple of px on each relayout, and a too-tight threshold here
            // means the next tick sees that as "still wrong" and relayouts
            // again, chasing its own noise instead of settling.
            var relayoutProps = {};
            if (Math.abs(gd._fullLayout.width - targetWidth) > 3) {
                relayoutProps.width = targetWidth;
            }
            if (Math.abs(gd._fullLayout.height - targetHeight) > 3) {
                relayoutProps.height = targetHeight;
            }
            if (Object.keys(relayoutProps).length) {
                Plotly.relayout(gd, relayoutProps);
            }
        });
    }

    setInterval(tick, 500);
    window.addEventListener("resize", tick);
})();

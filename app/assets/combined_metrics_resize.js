// Cumulative Metrics' 4 charts weren't picking up their CSS-driven container
// height via autosize + config.responsive alone. Forces the Plotly figure's
// own height/width to match the wrapper directly.
(function () {
    var IDS = ["combined-growth-epmc", "combined-citations-over-years", "combined-growth-github", "combined-growth-pypi"];

    function getPlotlyDiv(id) {
        var wrapper = document.getElementById(id);
        if (!wrapper) return null;
        return wrapper.querySelector(".js-plotly-plot");
    }

    function tick() {
        IDS.forEach(function (id) {
            var wrapper = document.getElementById(id);
            var gd = getPlotlyDiv(id);
            if (!wrapper || !gd || !gd._fullLayout) return;
            var targetHeight = wrapper.clientHeight;
            var targetWidth = wrapper.clientWidth;
            if (!targetHeight || !targetWidth) return;
            if (Math.abs(gd._fullLayout.height - targetHeight) > 2 || Math.abs(gd._fullLayout.width - targetWidth) > 2) {
                Plotly.relayout(gd, { height: targetHeight, width: targetWidth });
            }
        });
    }

    setInterval(tick, 500);
    window.addEventListener("resize", tick);
})();

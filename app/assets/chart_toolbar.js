// Click handling for chart_toolbar()'s download/reset buttons (ga4gh_theme.py).
(function () {
    var MAP_IDS = ["service_map", "epmc-countries-choropleth"];

    function getPlotlyDiv(id) {
        var wrapper = document.getElementById(id);
        if (!wrapper) return null;
        return wrapper.querySelector(".js-plotly-plot");
    }

    // Snapshot each map's initial geo layout before any pan/zoom, so reset
    // can relayout back to it instead of guessing default scale/center.
    var originalGeo = {};
    var pollId = setInterval(function () {
        var allCaptured = true;
        MAP_IDS.forEach(function (id) {
            if (originalGeo[id]) return;
            var gd = getPlotlyDiv(id);
            if (gd && gd.layout && gd.layout.geo) {
                originalGeo[id] = JSON.parse(JSON.stringify(gd.layout.geo));
            } else {
                allCaptured = false;
            }
        });
        if (allCaptured) clearInterval(pollId);
    }, 300);

    document.addEventListener("click", function (e) {
        var downloadBtn = e.target.closest(".chart-download-btn");
        if (downloadBtn) {
            var downloadId = downloadBtn.getAttribute("data-graph-id");
            var downloadGd = getPlotlyDiv(downloadId);
            if (downloadGd && window.Plotly) {
                Plotly.downloadImage(downloadGd, { format: "png", filename: downloadId });
            }
            return;
        }

        var resetBtn = e.target.closest(".chart-reset-btn");
        if (resetBtn) {
            var resetId = resetBtn.getAttribute("data-graph-id");
            var resetGd = getPlotlyDiv(resetId);
            if (resetGd && window.Plotly) {
                var snapshot = originalGeo[resetId];
                if (snapshot) {
                    Plotly.relayout(resetGd, { geo: JSON.parse(JSON.stringify(snapshot)) });
                } else {
                    Plotly.relayout(resetGd, { "geo.projection.scale": 1, "geo.center": null });
                }
            }
            return;
        }
    });
})();

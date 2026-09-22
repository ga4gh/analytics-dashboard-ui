// Chart "expand to fullscreen" pop-out — pairs with chart_expand_button() in
// ga4gh_theme.py and the #chart-modal markup/styling in home.py/style.css.
//
// Deliberately NOT a Dash clientside callback: there's one .chart-expand-btn
// per chart (24+ across the app), each wired only by a shared "chart-expand-
// btn" class and a data-graph-id attribute, so a single delegated listener
// on `document` covers all of them — new charts just need the button, no
// server callback or per-chart wiring. The clicked chart's live Plotly
// data/layout is cloned straight out of its own rendered DOM node into
// #chart-modal-graph via Plotly.newPlot, matching the look new_ga4gh's own
// image-modal component uses for photos (see style.css's .chart-modal rules).
(function () {
    function getPlotlyDiv(graphId) {
        var wrapper = document.getElementById(graphId);
        if (!wrapper) return null;
        // Dash's own id lands on the outer .dash-graph wrapper, not the
        // Plotly-initialized div one level inside — same quirk
        // map_zoom_clamp.js works around.
        return wrapper.querySelector(".js-plotly-plot") || wrapper;
    }

    function openModal(graphId, captionText) {
        var srcDiv = getPlotlyDiv(graphId);
        if (!srcDiv || !srcDiv.data || !window.Plotly) return;

        var data = JSON.parse(JSON.stringify(srcDiv.data));
        var layout = JSON.parse(JSON.stringify(srcDiv.layout || {}));
        layout.autosize = true;
        delete layout.width;
        delete layout.height;

        var captionEl = document.getElementById("chart-modal-caption");
        if (captionEl) captionEl.textContent = captionText || "";

        // Reveal the modal FIRST — Plotly.newPlot measures the target div's
        // current rendered size to lay out the figure. Calling it while the
        // modal (and therefore #chart-modal-graph) is still display:none
        // means it measures a 0×0 box, producing a wrongly-sized/positioned
        // plot once the modal actually becomes visible.
        document.getElementById("chart-modal").classList.add("chart-modal-open");

        var modalGraph = document.getElementById("chart-modal-graph");
        Plotly.newPlot(modalGraph, data, layout, { responsive: true, displaylogo: false });
        document.body.style.overflow = "hidden";
    }

    function closeModal() {
        var modal = document.getElementById("chart-modal");
        if (!modal || !modal.classList.contains("chart-modal-open")) return;
        modal.classList.remove("chart-modal-open");
        document.body.style.overflow = "";
        var modalGraph = document.getElementById("chart-modal-graph");
        if (window.Plotly && modalGraph) {
            Plotly.purge(modalGraph);
        }
    }

    document.addEventListener("click", function (e) {
        var expandBtn = e.target.closest(".chart-expand-btn");
        if (expandBtn) {
            var graphId = expandBtn.getAttribute("data-graph-id");
            var figure = expandBtn.closest("figure");
            var figcaption = figure && figure.querySelector("figcaption");
            openModal(graphId, figcaption ? figcaption.textContent : "");
            return;
        }

        if (e.target.closest(".chart-modal-close-trigger")) {
            closeModal();
            return;
        }

        // Click on the dark backdrop closes too — .chart-modal-content is the
        // full-height flex wrapper that centers .chart-modal-content-inner,
        // so it covers the entire backdrop area edge-to-edge; only a click
        // that actually lands on #chart-modal or that wrapper (never inside
        // .chart-modal-content-inner itself) counts as "outside the panel".
        if (e.target.id === "chart-modal" || e.target.classList.contains("chart-modal-content")) {
            closeModal();
        }
    });

    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") closeModal();
    });
})();

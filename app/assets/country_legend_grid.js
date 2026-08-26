// Sizes the countries pie's custom legend columns to exactly the widest
// entry's own rendered width. CSS Grid's auto-fit needs *some* definite
// track size to even compute how many columns fit — minmax(0, ...) sounds
// like "no floor", but a 0-wide track lets auto-fit compute a column for
// almost every item (one item per column, all squeezed into a single row),
// since technically infinite 0-width tracks "fit". The widest entry's width
// isn't knowable in pure CSS ahead of layout, so this measures it directly:
// each item's swatch + gap + its label's natural (unclipped, via
// scrollWidth) text width, takes the max across all of them, and sets that
// single value as every column's fixed width.
(function () {
    function fitLegendColumns() {
        var legend = document.getElementById("epmc-countries-legend");
        if (!legend) return;
        var items = legend.querySelectorAll(".country-legend-item");
        if (!items.length) return;

        var itemStyle = getComputedStyle(items[0]);
        var gapPx = parseFloat(itemStyle.columnGap || itemStyle.gap) || 0;

        var maxWidth = 0;
        items.forEach(function (item) {
            var label = item.querySelector(".country-legend-label");
            var swatch = item.querySelector(".country-legend-swatch");
            if (!label || !swatch) return;
            var needed = swatch.getBoundingClientRect().width + gapPx + label.scrollWidth;
            if (needed > maxWidth) maxWidth = needed;
        });

        if (maxWidth > 0) {
            legend.style.gridTemplateColumns = "repeat(auto-fit, " + Math.ceil(maxWidth) + "px)";
        }
    }

    // The legend's 35 items are rendered by a Dash callback (not present at
    // initial script load), and can also change size if country data itself
    // is ever refreshed — poll for its item count changing rather than a
    // one-shot run, same pattern as pie_autofit.js.
    var lastCount = -1;
    var lastWidth = -1;

    function tick() {
        var legend = document.getElementById("epmc-countries-legend");
        if (!legend) return;
        var count = legend.querySelectorAll(".country-legend-item").length;
        var width = legend.clientWidth;
        if (count !== lastCount || width !== lastWidth) {
            lastCount = count;
            lastWidth = width;
            fitLegendColumns();
        }
    }

    setInterval(tick, 500);
    window.addEventListener("resize", tick);
})();

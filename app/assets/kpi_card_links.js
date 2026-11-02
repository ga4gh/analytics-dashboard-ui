// KPI indicator cards (home.py's indicator_card()) navigate to a target
// section/chart on click via their data-kpi-target attribute. The YoY card
// also holds an interactive year dropdown, so clicks inside it don't navigate.
(function () {
    function scrollToTarget(card) {
        var targetId = card.getAttribute("data-kpi-target");
        var el = targetId && document.getElementById(targetId);
        if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    document.addEventListener("click", function (e) {
        if (e.target.closest(".yoy-year-dropdown")) return;
        var card = e.target.closest("[data-kpi-target]");
        if (card) scrollToTarget(card);
    });

    document.addEventListener("keydown", function (e) {
        if (e.key !== "Enter" && e.key !== " ") return;
        if (e.target.closest(".yoy-year-dropdown")) return;
        var card = e.target.closest("[data-kpi-target]");
        if (!card) return;
        e.preventDefault();
        scrollToTarget(card);
    });
})();

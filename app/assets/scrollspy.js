/* Highlights the sidebar nav link whose section is currently in view. */
(function () {
    var SECTION_IDS = [
        "overview",
        "servicemap",
        "metrics",
        "epmc",
        "publication-charts",
        "funder-only-charts",
        "github",
        "pypi",
        "developer-charts",
        "community-charts",
        "tables",
    ];

    var observer = null;

    function init() {
        var sections = SECTION_IDS
            .map(function (id) { return document.getElementById(id); })
            .filter(Boolean);
        var links = document.querySelectorAll(".left-nav-links .menu-link");

        if (!sections.length || !links.length) return;

        if (observer) observer.disconnect();

        function setActive(id) {
            links.forEach(function (a) {
                if (a.getAttribute("href") === "#" + id) {
                    a.classList.add("active");
                } else {
                    a.classList.remove("active");
                }
            });
        }

        observer = new IntersectionObserver(
            function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        setActive(entry.target.id);
                    }
                });
            },
            {
                root: null,
                rootMargin: "0px 0px -55% 0px",
                threshold: 0,
            }
        );

        sections.forEach(function (s) { observer.observe(s); });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

    /* Re-init when Dash updates the DOM (persona switching shows/hides sections). */
    var mo = new MutationObserver(function () { init(); });
    mo.observe(document.body, { childList: true, subtree: true });
})();

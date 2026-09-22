// Toggles the mobile nav dropdown open/closed. A plain click-delegated
// class toggle rather than <details>/<summary> (which doesn't reliably
// respect display:contents across browsers, hiding the nav on desktop).
(function () {
    document.addEventListener("click", function (e) {
        var trigger = e.target.closest(".mobile-menu-trigger");
        if (trigger) {
            var details = trigger.closest(".mobile-nav-details");
            if (details) details.classList.toggle("is-open");
            return;
        }
        // Clicking a nav link (or anywhere outside the panel) closes it.
        var openPanel = document.querySelector(".mobile-nav-details.is-open");
        if (openPanel && (!openPanel.contains(e.target) || e.target.closest(".menu-link"))) {
            openPanel.classList.remove("is-open");
        }
    });
})();

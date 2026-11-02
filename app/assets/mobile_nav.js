// Mobile hamburger nav toggle — pairs with #mobile-menu-toggle-btn and
// .menu-container's mobile dropdown-panel styling in style.css.
//
// new_ga4gh's own mobile nav uses a hidden checkbox + <label for=...> so the
// open/close state lives entirely in CSS (:checked). dash.html has no native
// <input>/<label> (those need dcc, which doesn't support type="checkbox"),
// so this reproduces the same visual behavior with a plain button whose
// click toggles a "mobile-nav-open" class on <body> instead — same
// click-outside-closes and Escape-closes behavior as their version.
(function () {
    function closeMenu() {
        document.body.classList.remove("mobile-nav-open");
    }

    function toggleMenu() {
        document.body.classList.toggle("mobile-nav-open");
    }

    document.addEventListener("click", function (e) {
        if (e.target.closest("#mobile-menu-toggle-btn")) {
            toggleMenu();
            return;
        }

        // Unlike new_ga4gh's own multi-page site (where navigating away
        // closes the menu for free via a full page load), this app jumps to
        // an in-page anchor with no reload — so a link click has to close
        // the panel itself, or it'd stay open over the section just
        // scrolled to.
        if (e.target.closest(".menu-link")) {
            closeMenu();
            return;
        }

        if (
            document.body.classList.contains("mobile-nav-open") &&
            !e.target.closest(".menu-container")
        ) {
            closeMenu();
        }
    });

    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") closeMenu();
    });
})();

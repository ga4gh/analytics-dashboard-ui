// .left-sidebar is position:fixed on desktop so it stays pinned to the
// viewport while scrolling through the (much taller) main content. But
// being fixed to the viewport rather than the page, it would keep
// rendering over the footer too once the footer scrolls into view. This
// swaps it to position:absolute — pinned to the document just above the
// footer's top edge — whenever the footer gets that close, and back to
// fixed the rest of the time.
// Desktop only — mobile's .left-sidebar is already position:sticky and
// naturally scrolls away before the footer via normal document flow.
(function () {
    var BREAKPOINT = "(pointer: coarse), (max-width: 768px)";

    function update() {
        var sidebar = document.querySelector(".left-sidebar");
        var footer = document.querySelector(".footer");
        if (!sidebar || !footer) return;

        if (window.matchMedia(BREAKPOINT).matches) {
            sidebar.style.position = "";
            sidebar.style.top = "";
            return;
        }

        var sidebarHeight = sidebar.offsetHeight;
        var footerTop = footer.getBoundingClientRect().top;

        if (footerTop < sidebarHeight) {
            var footerDocTop = footerTop + window.scrollY;
            sidebar.style.position = "absolute";
            sidebar.style.top = (footerDocTop - sidebarHeight) + "px";
        } else {
            sidebar.style.position = "fixed";
            sidebar.style.top = "0px";
        }
    }

    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    // Page height can also change with no scroll/resize event (e.g. a
    // persona switch showing/hiding whole chart sections), so poll too.
    setInterval(update, 500);
})();

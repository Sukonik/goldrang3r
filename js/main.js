/* BASE3 UI — behavior layer.
   Vanilla JS, no build step: drawer navigation + current-page marking.
   Structure and look live in the CSS layers; this file only moves state. */
(function () {
  "use strict";

  var page = location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".nav__link, .nav-drawer__link").forEach(function (a) {
    var href = (a.getAttribute("href") || "").split("/").pop();
    if (href === page) a.setAttribute("aria-current", "page");
  });

  var drawer = document.getElementById("nav-drawer");
  var toggle = document.querySelector(".nav-toggle");
  var closeBtn = document.querySelector(".nav-drawer__close");
  if (!drawer || !toggle) return;

  function setDrawer(open) {
    drawer.dataset.open = String(open);
    drawer.hidden = !open;
    document.body.dataset.drawerOpen = String(open);
    toggle.setAttribute("aria-expanded", String(open));
  }

  toggle.addEventListener("click", function () {
    setDrawer(drawer.dataset.open !== "true");
  });
  if (closeBtn) closeBtn.addEventListener("click", function () { setDrawer(false); });
  drawer.addEventListener("click", function (e) {
    if (e.target.closest("a")) setDrawer(false);
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && drawer.dataset.open === "true") setDrawer(false);
  });
})();

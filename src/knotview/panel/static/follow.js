/* Follow the backlog.
 *
 * The server streams one thing: a digest that moves when the backlog does. This asks for it, and when
 * it changes it reloads the page. Nothing here renders anything, which is the point: there is one
 * rendering path on the server, so what a reader sees after a change is exactly what they would see
 * on a fresh visit.
 *
 * The stream is one-way by construction and this sends nothing back. A panel that could write would
 * be a second author of a backlog that has one.
 */

(function follow() {
  var badge = document.getElementById("live");
  if (!badge || typeof EventSource === "undefined") return;

  var known = null;
  var stream = new EventSource("/live");

  stream.addEventListener("changed", function (event) {
    if (known === null) {
      known = event.data;
      badge.classList.add("following");
      return;
    }
    if (event.data !== known) {
      // Keep the scroll position across the reload, since a reader watching a long list while an
      // agent edits it should not be thrown back to the top every time.
      sessionStorage.setItem("knotview:scroll", String(window.scrollY));
      window.location.reload();
    }
  });

  stream.addEventListener("unreadable", function () {
    badge.textContent = "unreadable";
    badge.className = "live stale";
  });

  stream.onerror = function () {
    badge.textContent = "offline";
    badge.className = "live stale";
  };

  var was = sessionStorage.getItem("knotview:scroll");
  if (was !== null) {
    sessionStorage.removeItem("knotview:scroll");
    window.scrollTo(0, Number(was));
  }
})();

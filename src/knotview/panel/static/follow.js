// Follow the backlog.
//
// The server streams one thing: a digest that moves when the backlog does. This asks for it, and when
// it changes it reloads the page. Nothing here renders anything, which is the point: there is one
// rendering path on the server, so what a reader sees after a change is exactly what they would see
// on a fresh visit.
//
// The stream is one-way by construction and this sends nothing back. A panel that could write would
// be a second author of a backlog that has one.

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

// What changed since you last looked: per viewer, in this browser only, never sent anywhere.
// The last look is the instant of the previous page load; rows saved after it are marked and
// counted in the bar. Clicking the count makes now the last look.
(function () {
  var KEY = "knotview.lastLook";
  var since = document.getElementById("since");
  if (!since) return;
  var read = function () {
    try {
      return window.localStorage.getItem(KEY) || "";
    } catch (e) {
      return "";
    }
  };
  var write = function (value) {
    try {
      window.localStorage.setItem(KEY, value);
    } catch (e) {
      /* storage unavailable: the page still works, it just cannot remember */
    }
  };
  var last = read();
  var rows = document.querySelectorAll("tr[data-updated]");
  var count = 0;
  for (var i = 0; i < rows.length; i++) {
    var updated = rows[i].getAttribute("data-updated");
    if (last && updated && updated > last) {
      rows[i].classList.add("since-last-look");
      count++;
    }
  }
  if (count) {
    since.textContent = count + " since you last looked";
    since.hidden = false;
    since.addEventListener("click", function () {
      write(new Date().toISOString());
      window.location.reload();
    });
  }
  if (!last) write(new Date().toISOString());
})();

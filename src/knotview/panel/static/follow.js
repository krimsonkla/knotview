// Follow the backlog.
//
// The server streams one thing: a digest that moves when the backlog does. This asks for it, and when
// it changes it reloads the page. Nothing here adds content: there is one rendering path on the
// server, so what a reader sees after a change is exactly what they would see on a fresh visit. The
// last block restates instants the server already put in the markup, in the reader's own zone; it
// invents nothing.
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
// The last look is the instant of the first load, or of the last click on the count; rows
// saved after it are marked and counted in the bar.
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
  // Instants compared at one precision. knot writes microseconds and the browser writes
  // milliseconds, and between "…:00.123Z" and "…:00.123456Z" a string comparison puts the Z
  // above the digit, so a ticket saved later in the same millisecond read as older. Parsing
  // would not help: a Date holds milliseconds and the difference is below it. So the fraction
  // is padded to six digits on both sides and the padded strings compared. The browser's
  // millisecond look is zero-filled, which is the conservative side: a row saved earlier in
  // that same millisecond is marked too, and after a click it can stay marked once more. Only
  // knot's exact shape, a full instant ending in Z, is read; anything else compares as nothing,
  // so a changed shape would mark nothing rather than mark wrongly. Digits past the sixth are
  // dropped, so two rows a nanosecond apart compare equal.
  var padded = function (instant) {
    var found = /^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d+))?Z$/.exec(instant || "");
    if (!found) return null;
    return found[1] + "." + ((found[2] || "") + "000000").slice(0, 6) + "Z";
  };
  var lastAt = padded(read());
  var rows = document.querySelectorAll("tr[data-updated]");
  var count = 0;
  for (var i = 0; i < rows.length; i++) {
    var updatedAt = padded(rows[i].getAttribute("data-updated"));
    if (lastAt && updatedAt && updatedAt > lastAt) {
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
  // No last look, or one this cannot read: now becomes the last look.
  if (!lastAt) write(new Date().toISOString());
})();

// Instants in the reader's own zone. The server writes every instant as UTC with the zone named,
// which is right for a page without script and wrong for a reader in Berlin. Each `time.stamp`
// is restated here in the browser's zone, in the same fixed shape so a column still reads as one,
// and the title gains the zone it was restated in. A `time.ago` keeps its distance text and only
// gains the title: the distance is the information on that card. The two are told apart by class,
// so the distance text cannot be rewritten by mistake.
(function () {
  if (typeof Intl === "undefined" || typeof Intl.DateTimeFormat !== "function") return;
  if (typeof Intl.DateTimeFormat.prototype.formatToParts !== "function") return;
  var zone = "";
  try {
    zone = Intl.DateTimeFormat().resolvedOptions().timeZone || "";
  } catch (e) {
    zone = "";
  }
  var shape = new Intl.DateTimeFormat("en-CA", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZoneName: "short",
  });
  var restated = function (when) {
    var parts = shape.formatToParts(when);
    var got = {};
    for (var i = 0; i < parts.length; i++) got[parts[i].type] = parts[i].value;
    // Some engines write midnight as 24:00 under hour12: false.
    var hour = got.hour === "24" ? "00" : got.hour;
    var text = got.year + "-" + got.month + "-" + got.day + " " + hour + ":" + got.minute;
    return got.timeZoneName ? text + " " + got.timeZoneName : text;
  };
  var title = function (element) {
    var raw = element.getAttribute("datetime");
    element.title = zone ? raw + " · " + zone : raw;
  };
  var stamps = document.querySelectorAll("time.stamp[datetime]");
  for (var s = 0; s < stamps.length; s++) {
    var when = new Date(stamps[s].getAttribute("datetime"));
    if (isNaN(when.getTime())) continue;
    stamps[s].textContent = restated(when);
    title(stamps[s]);
  }
  var distances = document.querySelectorAll("time.ago[datetime]");
  for (var d = 0; d < distances.length; d++) title(distances[d]);
})();

// Follow the backlog.
//
// The server answers one thing: a digest that moves when the backlog does. This asks for it about
// once a second, and when it changes it reloads the page. Nothing here adds content: there is one
// rendering path on the server, so what a reader sees after a change is exactly what they would see
// on a fresh visit. The last block restates instants the server already put in the markup, in the
// reader's own zone; it invents nothing.
//
// A short request each time rather than a stream held open: a browser allows six connections to one
// host, and a stream per open tab used them up, so the seventh tab's page waited until one closed.
// A hidden tab stops asking, and asks at once when it is shown again. Only a GET is ever sent; a
// panel that could write would be a second author of a backlog that has one.

// Switch worktrees as soon as the dropdown changes, rather than waiting for a button. The form is
// an ordinary GET, so the page works the same without script, through its noscript button.
(function switcher() {
  var choice = document.getElementById("worktree-choice");
  if (!choice || !choice.form) return;
  choice.addEventListener("change", function () {
    choice.form.submit();
  });
})();

// Pin a tag when the pinned-tags field changes, as its own form does without script.
(function pinner() {
  var field = document.querySelector(".kv-pinned input[name=add]");
  if (!field || !field.form) return;
  field.addEventListener("change", function () {
    if (field.value.trim()) field.form.submit();
  });
})();

// A filter applies the moment it changes. The whole form is serialised, so a typed but
// unsubmitted search travels with a changed pill, and the location is replaced rather than
// pushed, so Back leaves the list. The script builds no URL of its own: the server answers a
// non-canonical query with a redirect to the one URL it builds itself.
(function filters() {
  var forms = document.querySelectorAll("form[data-auto]");
  for (var i = 0; i < forms.length; i++) {
    (function (form) {
      var go = function () {
        var query = new URLSearchParams(new FormData(form)).toString();
        window.location.replace(form.getAttribute("action") + (query ? "?" + query : ""));
      };
      // A change inside the More filters dialog waits for its Apply button, so several boxes can
      // be ticked before the list reloads.
      form.addEventListener("change", function (event) {
        if (event.target.closest("dialog")) return;
        go();
      });
      form.addEventListener("submit", function (event) {
        event.preventDefault();
        go();
      });
      // The dialog opens from its button; Cancel and Escape put the form back to what the page
      // applied, so nothing chosen and then cancelled rides along with a later change.
      var buttons = form.querySelectorAll("[data-open], [data-close]");
      for (var b = 0; b < buttons.length; b++) {
        buttons[b].addEventListener("click", function (event) {
          var name = event.currentTarget.getAttribute("data-open");
          var dialogs = form.getElementsByTagName("dialog");
          for (var d = 0; d < dialogs.length; d++) {
            if (name && dialogs[d].id === name) dialogs[d].showModal();
            if (!name && dialogs[d].open) {
              form.reset();
              dialogs[d].close();
            }
          }
        });
      }
      var held = form.getElementsByTagName("dialog");
      for (var h = 0; h < held.length; h++) {
        held[h].addEventListener("cancel", function () {
          form.reset();
        });
      }
    })(forms[i]);
  }
})();

// A search typed but not yet submitted survives the reload a backlog change causes: it is kept
// for this path in this tab, put back once, and forgotten.
var searchKey = "knotview:search:" + window.location.pathname;
var keepSearch = function () {
  var box = document.querySelector("form[data-auto] input[name=q]");
  try {
    if (box && box.value !== box.defaultValue) sessionStorage.setItem(searchKey, box.value);
  } catch (e) {
    /* storage unavailable: the typed text is lost on reload, as before */
  }
};
(function restoreSearch() {
  var box = document.querySelector("form[data-auto] input[name=q]");
  try {
    var kept = sessionStorage.getItem(searchKey);
    if (kept !== null) {
      sessionStorage.removeItem(searchKey);
      if (box) box.value = kept;
    }
  } catch (e) {
    /* same */
  }
})();

// The theme switch cycles System, Light and Dark. A choice is kept in this browser and set as the
// page's data-theme, which the stylesheets read; System removes both and follows the computer.
(function themes() {
  var ORDER = ["system", "light", "dark"];
  var SAYS = {
    system: "Theme: follows the system. Click for light.",
    light: "Theme: light. Click for dark.",
    dark: "Theme: dark. Click to follow the system.",
  };
  var root = document.documentElement;
  var buttons = document.querySelectorAll("[data-theme-toggle]");
  var current = function () {
    return root.dataset.theme === "light" || root.dataset.theme === "dark"
      ? root.dataset.theme
      : "system";
  };
  var label = function () {
    for (var i = 0; i < buttons.length; i++) buttons[i].title = SAYS[current()];
  };
  for (var b = 0; b < buttons.length; b++) {
    buttons[b].addEventListener("click", function () {
      var next = ORDER[(ORDER.indexOf(current()) + 1) % ORDER.length];
      if (next === "system") delete root.dataset.theme;
      else root.dataset.theme = next;
      try {
        if (next === "system") localStorage.removeItem("knotview.theme");
        else localStorage.setItem("knotview.theme", next);
      } catch (e) {
        /* storage unavailable: the choice lasts for this page only */
      }
      label();
    });
  }
  label();
})();

(function follow() {
  var badge = document.getElementById("live");
  if (!badge || typeof fetch === "undefined") return;

  var EVERY = 1000;
  var LONGEST = 30000;
  var wait = EVERY;
  // The digest the page was rendered under, when the server could read one. Starting from it
  // rather than from the first answer means a change that lands before the first answer, such as
  // a worktree switched in another tab, still reloads this page. Without it, the first answer is
  // the baseline, as before.
  var known = badge.getAttribute("data-digest");
  var timer = null;
  var asking = false;

  var mark = function (text, stale) {
    badge.textContent = text;
    badge.classList.toggle("stale", Boolean(stale));
  };

  var ask = function () {
    timer = null;
    // A page that carries no digest asks once even while hidden: the first answer records what it
    // was rendered from, so a tab opened in the background still reloads when shown after a change.
    if ((document.hidden && known !== null) || asking) return;
    asking = true;
    fetch("/digest", { cache: "no-store" })
      .then(function (answer) {
        if (!answer.ok) {
          mark("unreadable", true);
          wait = Math.min(wait * 2, LONGEST);
          return null;
        }
        wait = EVERY;
        return answer.text();
      })
      .then(function (digest) {
        asking = false;
        if (digest === null) {
          later();
          return;
        }
        if (known === null) {
          known = digest;
          mark("live", false);
        } else if (digest !== known) {
          // Keep the scroll position across the reload, since a reader watching a long list while
          // an agent edits it should not be thrown back to the top every time.
          sessionStorage.setItem("knotview:scroll", String(window.scrollY));
          keepSearch();
          window.location.reload();
          return;
        } else {
          mark("live", false);
        }
        later();
      })
      .catch(function () {
        asking = false;
        mark("offline", true);
        // A panel that has stopped is asked less and less often, up to twice a minute.
        wait = Math.min(wait * 2, LONGEST);
        later();
      });
  };

  var later = function () {
    if (timer === null && !document.hidden) timer = setTimeout(ask, wait);
  };

  document.addEventListener("visibilitychange", function () {
    if (!document.hidden && timer === null) ask();
  });

  var was = sessionStorage.getItem("knotview:scroll");
  if (was !== null) {
    sessionStorage.removeItem("knotview:scroll");
    window.scrollTo(0, Number(was));
  }
  ask();
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
  var rows = document.querySelectorAll("[data-updated]");
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

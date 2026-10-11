// Which folds a reader opened, and which tab they chose, kept in this browser only. Nothing here
// talks to the server: folding is a fact about the reader, not the backlog.
//
// A `details[data-fold]` remembers in localStorage, so the tree keeps its folds across visits,
// unless it asks for the session with data-fold-store="session", so a ticket page's sections
// last for the tab. Stored ids and the URL hash are untrusted: they are only ever compared with
// ids this page rendered, never turned into a selector or into markup.
(function () {
  var store = function (node) {
    try {
      return node.getAttribute("data-fold-store") === "session"
        ? window.sessionStorage
        : window.localStorage;
    } catch (e) {
      return null;
    }
  };
  var key = function (node) {
    return "knotview.fold." + node.getAttribute("data-fold");
  };
  var folds = document.querySelectorAll("details[data-fold]");
  for (var i = 0; i < folds.length; i++) {
    var node = folds[i];
    var held = store(node);
    try {
      var was = held ? held.getItem(key(node)) : null;
      if (was === "open") node.setAttribute("open", "");
      if (was === "closed") node.removeAttribute("open");
    } catch (e) {
      /* storage unavailable: the fold keeps its rendered state */
    }
    node.addEventListener("toggle", function (event) {
      var target = event.target;
      var where = store(target);
      try {
        if (where) where.setItem(key(target), target.open ? "open" : "closed");
      } catch (e) {
        /* same */
      }
    });
  }

  // Charts: each checkbox shows or hides the chart it names, remembered in localStorage. A name
  // is only ever compared with the charts this page drew.
  var charts = document.querySelectorAll("section[data-chart]");
  var toggles = document.querySelectorAll("input[data-chart-toggle]");
  var chartKey = function (name) {
    return "knotview.chart." + name;
  };
  var showChart = function (name, on) {
    for (var c = 0; c < charts.length; c++) {
      if (charts[c].getAttribute("data-chart") === name) charts[c].hidden = !on;
    }
  };
  for (var t = 0; t < toggles.length; t++) {
    var box = toggles[t];
    var name = box.getAttribute("data-chart-toggle");
    try {
      var saved = window.localStorage.getItem(chartKey(name));
      if (saved !== null) box.checked = saved === "on";
    } catch (e) {
      /* storage unavailable: the page's defaults stand */
    }
    showChart(name, box.checked);
    box.addEventListener("change", function (event) {
      var which = event.target.getAttribute("data-chart-toggle");
      showChart(which, event.target.checked);
      try {
        window.localStorage.setItem(chartKey(which), event.target.checked ? "on" : "off");
      } catch (e) {
        /* same */
      }
    });
  }

  // Tabs: a bar of links, each naming a panel by id. The hash picks one when it names a panel
  // this page drew; anything else picks the first. A choice replaces the history entry.
  var bar = document.querySelector("[data-tabs]");
  if (!bar) return;
  var links = bar.getElementsByTagName("a");
  var panels = document.getElementsByClassName("kv-tabpanel");
  var show = function (wanted) {
    var found = false;
    for (var p = 0; p < panels.length; p++) if (panels[p].id === wanted) found = true;
    if (!found) wanted = panels.length ? panels[0].id : "";
    for (var q = 0; q < panels.length; q++) panels[q].hidden = panels[q].id !== wanted;
    for (var l = 0; l < links.length; l++) {
      links[l].setAttribute(
        "aria-selected",
        links[l].getAttribute("data-tab") === wanted ? "true" : "false",
      );
    }
  };
  for (var l = 0; l < links.length; l++) {
    links[l].addEventListener("click", function (event) {
      event.preventDefault();
      var wanted = event.currentTarget.getAttribute("data-tab");
      window.location.replace("#" + wanted);
      show(wanted);
    });
  }
  show(window.location.hash.slice(1));
})();

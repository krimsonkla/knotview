// The tree page remembers which branches a reader folded, in this browser only.
// Nothing here talks to the server: folding is a fact about the reader, not the backlog.
(function () {
  var key = function (node) {
    return "knotview.fold." + node.getAttribute("data-fold");
  };
  var folds = document.querySelectorAll("details[data-fold]");
  for (var i = 0; i < folds.length; i++) {
    var node = folds[i];
    try {
      if (window.localStorage.getItem(key(node)) === "closed") {
        node.removeAttribute("open");
      }
    } catch (e) {
      /* storage may be unavailable; the tree still works unfolded */
    }
    node.addEventListener("toggle", function (event) {
      try {
        window.localStorage.setItem(
          key(event.target),
          event.target.open ? "open" : "closed",
        );
      } catch (e) {
        /* same */
      }
    });
  }
})();

// Bring the current document's tab into view when the row of tabs is wider than the page.
// A convenience only: without it the row still scrolls, and the "all" menu lists every document.
// Run once the page has laid out, since the row's width is not final before then.
window.addEventListener("load", () => {
  document
    .querySelector(".tabs [aria-current]")
    ?.scrollIntoView({ block: "nearest", inline: "nearest" });
});

/* Costuras Lucía — keep admin light-only (stale Alpine persist / Ctrl+E could flip <html>). */
(function () {
  var html = document.documentElement;

  function stripDark() {
    if (html.classList.contains("dark")) {
      html.classList.remove("dark");
      html.classList.add("light");
    }
  }

  stripDark();

  try {
    Object.keys(localStorage).forEach(function (k) {
      if (/admintheme/i.test(k)) localStorage.removeItem(k);
    });
  } catch (_) {}

  if (typeof MutationObserver !== "undefined") {
    new MutationObserver(stripDark).observe(html, {
      attributes: true,
      attributeFilter: ["class"],
    });
  }
})();

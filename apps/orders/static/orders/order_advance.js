/**
 * POST /admin/orders/order/<id>/advance/ with CSRF cookie (Unfold admin lists).
 */
(function () {
  function getCookie(name) {
    var v = null;
    document.cookie.split(";").forEach(function (c) {
      var p = c.trim().split("=");
      if (p[0] === name) v = decodeURIComponent(p[1]);
    });
    return v;
  }

  document.body.addEventListener("click", function (e) {
    var btn = e.target.closest(".js-order-advance");
    if (!btn) return;
    e.preventDefault();
    var url = btn.getAttribute("data-advance-url");
    if (!url) return;
    var token = getCookie("csrftoken");
    fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: token
        ? {
            "X-CSRFToken": token,
            Accept: "application/json",
          }
        : { Accept: "application/json" },
    })
      .then(function (r) {
        if (r.ok) {
          window.location.reload();
          return;
        }
        return r.json().then(function (d) {
          var err = (d && (d.error || d.detail)) || r.statusText;
          alert(err);
        });
      })
      .catch(function () {
        alert("Network error");
      });
  });
})();

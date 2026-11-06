/* IV Infotech lead page: the only script. (1) the calculator, (2) the big play button on the video, (3) the sticky WhatsApp bar on phones.
   The only network traffic is the first-party beacon (a GET for e.gif on our own server: no cookies, no third party). (build_site_pages.py prefixes the
   ids and the class names for the ivinfotech.com build, so look elements up through $() / classList only.) */
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById("cp-" + id); };

  // ---- first-party beacons: a tiny GET for e.gif?e=<event> lands in OUR OWN web log (no cookie, no third party). The owner's follow-up
  // view reads them: play, how far the video went, which button was clicked, calculator / FAQ used. Never blocks the page.
  var SRC = document.currentScript && document.currentScript.src;
  var BEACON = SRC ? SRC.replace(/page\.js.*$/, "e.gif") : "";
  var sent = {};
  var beacon = function (name, once) {
    if (!BEACON || (once && sent[name])) { return; }
    sent[name] = true;
    try {
      var url = BEACON + "?e=" + encodeURIComponent(name) + "&_=" + Date.now();
      if (window.fetch) { fetch(url, { method: "GET", keepalive: true, mode: "no-cors", cache: "no-store" }).catch(function () {}); } else { new Image().src = url; }
    } catch (err) { /* a beacon must never break the page */ }
  };
  var inr = function (n) { return Math.round(n).toLocaleString("en-IN"); };
  var one = function (n) { return (Math.round(n * 10) / 10).toLocaleString("en-IN", { maximumFractionDigits: 1 }); };
  var RUPEE = "₹";

  // ---- calculator: every number is the visitor's own; the formula is printed under the results and the two assumptions are labelled as examples
  var enq = $("c-enq"), late = $("c-late"), cost = $("c-cost");
  if (enq && late && cost) {
    var fill = function (el) { var pct = (el.value - el.min) / (el.max - el.min) * 100; el.style.setProperty("--pct", pct + "%"); };
    var update = function () {
      var e = +enq.value, l = +late.value, c = +cost.value;
      var waiting = e * l / 100;                                   // enquiries that wait more than an hour for the first reply
      $("o-enq").textContent = inr(e);
      $("o-late").textContent = l;
      $("o-cost").textContent = RUPEE + inr(c);
      $("r-late").textContent = one(waiting);
      $("r-cost").textContent = "About " + RUPEE + inr(waiting * c) + " of ad spend";
      $("r-visits").textContent = one(waiting / 10);               // example assumption: 1 in 10 of them would still visit
      $("r-hours").textContent = one(e * 3 / 60);                  // example assumption: 3 minutes of team time per first reply
      [enq, late, cost].forEach(fill);
    };
    [enq, late, cost].forEach(function (el) { el.addEventListener("input", function () { beacon("calc", true); update(); }); });
    update();
  }

  // ---- video: a big play button (the tiny native triangle is hard to find); the native controls appear after the first tap
  var wrap = $("vwrap"), vid = $("demo-video"), vbtn = $("vplay");
  if (wrap && vid && vbtn) {
    vid.removeAttribute("controls");
    wrap.classList.add("cp-vjs");
    vbtn.addEventListener("click", function () {
      beacon("play_button", true);
      vid.setAttribute("controls", "");
      wrap.classList.add("cp-playing");
      var p = vid.play();
      if (p && p.catch) { p.catch(function () {}); }
    });
  }

  if (vid) {
    vid.addEventListener("play", function () { beacon("play", true); });
    vid.addEventListener("timeupdate", function () {
      if (!vid.duration) { return; }
      var p = vid.currentTime / vid.duration;
      if (p >= 0.25) { beacon("p25", true); }
      if (p >= 0.5) { beacon("p50", true); }
      if (p >= 0.75) { beacon("p75", true); }
    });
    vid.addEventListener("ended", function () { beacon("end", true); });
  }
  [["cta-hero", "cta_hero"], ["cta-final", "cta_final"]].forEach(function (pair) {
    var el = $(pair[0]);
    if (el) { el.addEventListener("click", function () { beacon(pair[1], false); }); }
  });
  var stickyEl = $("sticky");                                         // by id (the site build prefixes ids), never by a raw "#sticky" selector
  var stickyLink = stickyEl && stickyEl.querySelector("a");
  if (stickyLink) { stickyLink.addEventListener("click", function () { beacon("cta_sticky", false); }); }
  Array.prototype.forEach.call(document.querySelectorAll("details"), function (d) { d.addEventListener("toggle", function () { if (d.open) { beacon("faq", true); } }); });

  // ---- phones: show the sticky WhatsApp button only when no main button and no video is on screen
  var sticky = $("sticky"), hero = $("cta-hero"), fin = $("cta-final");
  if (sticky && hero && "IntersectionObserver" in window) {
    var visible = { hero: true, fin: false, vid: false };
    var apply = function () { sticky.classList.toggle("cp-show", !visible.hero && !visible.fin && !visible.vid); };
    new IntersectionObserver(function (es) { visible.hero = es[0].isIntersecting; apply(); }).observe(hero);
    // final button dikh raha ho YA uske neeche (footer tak) pahunch gaye ho -> sticky bar chhupa do, taaki footer ke links na dhakein
    if (fin) new IntersectionObserver(function (es) { visible.fin = es[0].isIntersecting || es[0].boundingClientRect.top < 0; apply(); }).observe(fin);
    if (wrap) new IntersectionObserver(function (es) { visible.vid = es[0].isIntersecting; apply(); }, { threshold: 0.2 }).observe(wrap);
  }
})();

/* PSL TERMINAL client runtime.
   Command line + keyboard: CODE⏎ maximises a panel, Esc restores, digits jump,
   letters K D A S R P open the hidden pages. The equity panel renders on
   TradingView Lightweight Charts (vendored, assets/vendor/, Apache-2.0); every
   other chart is drawn here as SVG from the specification the server puts in
   a data-spec attribute, so the page needs no plotting library. Time on the
   equity panel is a simulated month, never a calendar date of the real world.
   The stream store fans out ticks, headlines, alerts and ledger entries pushed
   by the poll. */
(function () {
  "use strict";

  var CODES = ["NWS", "MKT", "SAF", "PNL", "WLF", "GAP", "LDG", "RUN", "ASK", "POL", "RSK", "DAT", "AGT", "SEC", "REG"];
  var DIGITS = { "1": "NWS", "2": "MKT", "3": "SAF", "4": "PNL", "5": "WLF", "6": "GAP", "7": "LDG", "8": "RUN", "9": "ASK", "0": "POL" };
  var LETTERS = { k: "RSK", d: "DAT", a: "AGT", s: "SEC", r: "REG", p: "POL", g: "GRID", h: "FRONT" };
  var AMBER = "#f6b52a", WHITE = "#e4e9f2", MUTED = "#5d6a80", HAIR = "rgba(148,163,196,.30)",
      INFO = "#6cb5ff", BAD = "#ff5f5f", GOOD = "#47d6a3", GRIDLINE = "rgba(148,163,196,.10)", TEXT = "#97a3b8";
  var PALETTE = ["#f6b52a", "#6cb5ff", "#47d6a3", "#ff5f5f", "#c792ea", "#ffd166", "#4cc9f0", "#f28482", "#9bc53d", "#e0aaff"];

  var st = {
    chart: null, series: [], labels: [], polLabels: {},
    pols: {}, order: [], live: null, shown: null, follow: true, nwsShown: "__live__",
    heads: [], mode: "px", nwsMode: "wire", evaluated: null, runId: null,
    tickerItems: [], ledgerCount: 0, headCount: 0, lastDate: null, lastPressure: null, lastTrust: null,
    maxed: null, selKnown: {}
  };
  window.__pslState = st;   // read only, for diagnostics

  function $(id) { return document.getElementById(id); }
  function clearNative(inp) {
    var set = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
    set.call(inp, "");
    inp.dispatchEvent(new Event("input", { bubbles: true }));
  }

  /* ------------------------------------------------ maximise / grid -- */
  function maximise(code) {
    if (CODES.indexOf(code) < 0) return false;
    restore();
    var p = $("panel-" + code);
    if (!p) return false;
    p.classList.add("maxed");
    document.body.classList.add("hasmax");
    st.maxed = code;
    setTimeout(function () { fitShown(); redrawCharts(true); }, 60);
    return true;
  }
  function restore() {
    if (st.maxed) {
      var p = $("panel-" + st.maxed);
      if (p) p.classList.remove("maxed");
    }
    document.body.classList.remove("hasmax");
    st.maxed = null;
    setTimeout(function () { fitShown(); redrawCharts(true); }, 60);
  }
  function flash(msg, ok) {
    var el = $("cmd-msg");
    if (!el) return;
    el.textContent = msg;
    el.className = ok ? "ok" : "err";
    clearTimeout(flash._t);
    flash._t = setTimeout(function () { el.textContent = ""; }, 2600);
  }
  function frontEl() { return $("front"); }
  function frontOpen() { var f = frontEl(); return f && !f.classList.contains("off"); }
  function showFront() { var f = frontEl(); if (f) f.classList.remove("off"); }
  function hideFront() { var f = frontEl(); if (f) f.classList.add("off"); }

  function exec(raw) {
    var c = (raw || "").toUpperCase().replace(/<GO>|\s/g, "");
    if (!c) return;
    if (c === "FRONT" || c === "100") {
      restore(); showFront(); flash("Front page", true);
      if (document.activeElement) document.activeElement.blur();
      return;
    }
    if (c === "GRID" || c === "ESC" || c === "HOME") { hideFront(); restore(); if (window.PSL_ASK) window.PSL_ASK.close(); flash("Grid", true); return; }
    if (c === "HELP") { flash("CODE then GO opens a page; digits 0 to 9 and K D A S R P; Esc restores the grid; drag the lines between boxes to resize; LAYOUT resets", true); return; }
    if (c === "ASK" || c === "BOT" || c === "CHAT" || c === "ORACLE" || c === "9") {
      hideFront(); restore();
      if (window.PSL_ASK) window.PSL_ASK.open();
      flash("ASK", true); return;
    }
    if (c === "RUNS" || c === "HIST" || c === "REGISTRY") c = "REG";
    if (c === "RISK" || c === "ASSURE" || c === "ASSURANCE" || c === "TORNADO" || c === "RED") c = "RSK";
    if (c === "DATA" || c === "UPLOAD" || c === "DESK") c = "DAT";
    if (c === "SECURITY" || c === "POSTURE") c = "SEC";
    if (c === "POLICY" || c === "POLICIES" || c === "LIB" || c === "LIBRARY" || c === "INSTRUMENTS") c = "POL";
    if (c === "FIRMS" || c === "FIRM" || c === "AGENT" || c === "AGENTS" || c === "WORKSHOP") c = "AGT";
    if (c === "NEWS" || c === "WIRE" || c === "PRESS") c = "NWS";
    if (c === "STOCKS" || c === "EQUITY" || c === "EQUITIES" || c === "PRICES" || c === "MARKET") c = "MKT";
    if (c === "SAFETY" || c === "HARM" || c === "RISKS") c = "SAF";
    if (c === "INDUSTRY" || c === "FIRMSPNL" || c === "GAIN" || c === "LOSS") c = "PNL";
    if (c === "WELFARE" || c === "SOCIAL" || c === "LEDGER" && false) c = "WLF";
    if (c === "COST" || c === "COSTS" || c === "WATERFALL") c = "WLF";
    if (c === "DECISION" || c === "RANK" || c === "RANKS") c = "GAP";
    if (c === "CHAIN" || c === "RATIONALE") c = "LDG";
    if (c === "CONTROL" || c === "GATES" || c === "GATE") c = "RUN";
    if (c === "LAYOUT" || c === "RESET") { window.pslResetLayout && window.pslResetLayout(); return; }
    if (DIGITS[c]) c = DIGITS[c];
    if (c === "ASK") { exec("ASK"); return; }
    if (window.PSL_ASK) window.PSL_ASK.close();          // a page opens from anywhere, including from ASK
    if (maximise(c)) { hideFront(); flash(c + " maximised", true); }
    else { flash("Unknown function " + c.slice(0, 12), false); }
  }
  window.pslExec = exec;

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      hideFront(); restore();
      if (window.PSL_ASK) window.PSL_ASK.close();
      if (document.activeElement && document.activeElement.id === "cmd") {
        clearNative(document.activeElement);
        document.activeElement.blur();
      }
      return;
    }
    var t = e.target, typing = t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" ||
      t.tagName === "SELECT" || t.isContentEditable);
    if (t && t.id === "cmd" && e.key === "Enter") { exec(t.value); clearNative(t); t.blur(); e.preventDefault(); return; }
    if (frontOpen() && !typing && e.key === "Enter") { hideFront(); e.preventDefault(); return; }
    if (typing || e.ctrlKey || e.metaKey || e.altKey) return;
    if (/^[0-9]$/.test(e.key)) { exec(e.key); e.preventDefault(); return; }
    var letter = LETTERS[e.key.toLowerCase()];
    if (letter && !e.shiftKey) { exec(letter); e.preventDefault(); }
  }, true);

  document.addEventListener("click", function (e) {
    if (!frontOpen()) return;
    var b = e.target.closest ? e.target.closest("#fenter,#frun,.slot") : null;
    if (!b) return;
    if (b.id === "fenter") { hideFront(); }
    else if (b.id === "frun") { hideFront(); exec("RUN"); }
    else if (b.dataset && b.dataset.code) { exec(b.dataset.code); }
  }, true);

  document.addEventListener("click", function (e) {
    var k = e.target.closest ? e.target.closest("button.fkey") : null;
    if (!k || !k.dataset.code) return;
    exec(k.dataset.code);
  });

  // drag handles between panels and between rows; the sizes live in the flex
  // basis of the neighbours, so the layout stays a plain flex layout
  (function () {
    var drag = null;
    function flexOf(el) { var f = parseFloat(getComputedStyle(el).flexGrow); return isNaN(f) ? 1 : f; }
    document.addEventListener("pointerdown", function (e) {
      var g = e.target.closest ? e.target.closest(".gutter") : null;
      if (!g) return;
      var prev = g.previousElementSibling, next = g.nextElementSibling;
      while (prev && prev.classList.contains("gutter")) prev = prev.previousElementSibling;
      while (next && next.classList.contains("gutter")) next = next.nextElementSibling;
      if (!prev || !next) return;
      var vertical = g.classList.contains("gutter-v");
      var a = vertical ? prev.getBoundingClientRect().width : prev.getBoundingClientRect().height;
      var b = vertical ? next.getBoundingClientRect().width : next.getBoundingClientRect().height;
      drag = { g: g, prev: prev, next: next, vertical: vertical, start: vertical ? e.clientX : e.clientY,
               a: a, b: b, total: a + b, grow: flexOf(prev) + flexOf(next) };
      g.classList.add("dragging");
      document.body.classList.add(vertical ? "resizing" : "resizing-h");
      g.setPointerCapture && g.setPointerCapture(e.pointerId);
      e.preventDefault();
    });
    document.addEventListener("pointermove", function (e) {
      if (!drag) return;
      var d = (drag.vertical ? e.clientX : e.clientY) - drag.start;
      var min = drag.vertical ? 160 : 90;
      var a = Math.max(min, Math.min(drag.total - min, drag.a + d));
      var b = drag.total - a;
      drag.prev.style.flex = (drag.grow * a / drag.total) + " 1 0";
      drag.next.style.flex = (drag.grow * b / drag.total) + " 1 0";
    });
    function end() {
      if (!drag) return;
      drag.g.classList.remove("dragging");
      document.body.classList.remove("resizing", "resizing-h");
      drag = null;
      window.dispatchEvent(new Event("resize"));      // charts redraw to the new box
    }
    document.addEventListener("pointerup", end);
    document.addEventListener("pointercancel", end);
    document.addEventListener("dblclick", function (e) {
      var g = e.target.closest ? e.target.closest(".gutter") : null;
      if (!g) return;
      var row = g.parentElement;
      row.querySelectorAll(":scope > .panel, :scope > .trow").forEach(function (p) { p.style.flex = ""; });
      window.dispatchEvent(new Event("resize"));
    });
    window.pslResetLayout = function () {
      document.querySelectorAll(".trow, .trow > .panel").forEach(function (p) { p.style.flex = ""; });
      window.dispatchEvent(new Event("resize"));
    };
  })();

  // sectioned panel bodies: the selection survives the server's re-renders
  var SEC = {};
  function applySec(body) {
    if (!body) return;
    var want = SEC[body.id] || "0";
    var btns = body.querySelectorAll(".sec-btn"), secs = body.querySelectorAll(".sec");
    if (!btns.length) return;
    var found = false;
    btns.forEach(function (b) { if (b.dataset.sec === want) found = true; });
    if (!found) want = "0";
    btns.forEach(function (b) { b.classList.toggle("on", b.dataset.sec === want); });
    secs.forEach(function (s) { s.classList.toggle("on", s.dataset.sec === want); });
  }
  document.addEventListener("click", function (e) {
    var b = e.target.closest ? e.target.closest("button.sec-btn") : null;
    if (!b) return;
    var body = b.closest(".p-body");
    if (!body) return;
    SEC[body.id] = b.dataset.sec;
    applySec(body);
    redrawCharts(true);
  });
  var secObs = new MutationObserver(function (muts) {
    var seen = {};
    muts.forEach(function (m) {
      var body = m.target.closest ? m.target.closest(".p-body") : null;
      if (body && !seen[body.id]) { seen[body.id] = true; applySec(body); }
    });
    scheduleCharts();
  });
  function observeBodies() {
    document.querySelectorAll(".p-body").forEach(function (b) {
      if (b.__obs) return;
      b.__obs = true;
      secObs.observe(b, { childList: true, subtree: true });
    });
  }

  // identifiers shown to the official: underscores to spaces, sentence case
  var ACR = { ai: "AI", us: "US", eu: "EU", uk: "UK", npv: "NPV", pe: "PE", rd: "R&D" };
  function nice(s) {
    s = String(s);
    if (!/^[A-Za-z][A-Za-z0-9]*(_[A-Za-z0-9]+)+$/.test(s)) return s;
    return s.split("_").map(function (w, i) {
      var l = w.toLowerCase();
      if (ACR[l]) return ACR[l];
      return i === 0 ? w.charAt(0).toUpperCase() + w.slice(1) : w;
    }).join(" ");
  }
  window.pslNice = nice;
  function polLabel(name) { return st.polLabels[name] || nice(name); }

  document.addEventListener("dblclick", function (e) {
    var head = e.target.closest && e.target.closest(".p-head");
    if (!head) return;
    var panel = head.parentElement, code = panel && panel.dataset.code;
    if (!code) return;
    if (st.maxed === code) restore(); else exec(code);
  });

  /* ------------------------------------------------- equity panel -- */
  function chartOpts(el) {
    return {
      autoSize: true,
      layout: { background: { color: "transparent" }, textColor: TEXT, fontSize: 10,
                fontFamily: "JetBrains Mono, ui-monospace, Menlo, Consolas, monospace", attributionLogo: false },
      grid: { vertLines: { color: GRIDLINE }, horzLines: { color: GRIDLINE } },
      crosshair: { mode: 0,
        vertLine: { color: AMBER, width: 1, style: 3, labelBackgroundColor: "#b5821a" },
        horzLine: { color: AMBER, width: 1, style: 3, labelBackgroundColor: "#b5821a" } },
      localization: { timeFormatter: function (t) { return dateOf(t); } },
      timeScale: { borderColor: HAIR, timeVisible: false, secondsVisible: false,
                   tickMarkFormatter: function (t) { return dateOf(t); } },
      rightPriceScale: { borderColor: HAIR },
      el: el
    };
  }
  var DATES = {};
  function dateOf(t) { return DATES[t] || ("m" + t); }

  function ensureChart() {
    if (st.chart) return true;
    if (typeof LightweightCharts === "undefined") return false;
    var el = $("mkt-chart");
    if (!el || !el.clientWidth) return false;
    st.chart = LightweightCharts.createChart(el, chartOpts(el));
    if (st.labels.length) buildSeries();
    if (st.shown) show(st.shown, true);
    return true;
  }
  function buildSeries() {
    if (!st.chart) return;
    st.series.forEach(function (s) { try { st.chart.removeSeries(s); } catch (e) { /* gone */ } });
    st.series = st.labels.map(function (lab, i) {
      return st.chart.addSeries(LightweightCharts.LineSeries, {
        color: PALETTE[i % PALETTE.length], lineWidth: 1, title: "",
        priceFormat: { type: "price", precision: 1, minMove: 0.1 },
        lastValueVisible: true, priceLineVisible: false, crosshairMarkerVisible: true
      });
    });
    var lg = $("mkt-legend");
    if (lg) {
      lg.innerHTML = "";
      st.labels.forEach(function (lab, i) {
        var s = document.createElement("span"); s.className = "lg";
        var sw = document.createElement("i"); sw.style.background = PALETTE[i % PALETTE.length];
        s.appendChild(sw); s.appendChild(document.createTextNode(lab));
        lg.appendChild(s);
      });
    }
  }

  function show(name, force) {
    var pol = st.pols[name];
    if (!pol || !st.chart || !st.series.length) { st.shown = name; return; }
    if (st.shown === name && !force) return;
    st.shown = name;
    st.series.forEach(function (s, i) { s.setData(pol.pts[i] || []); });
    st.chart.timeScale().fitContent();
    setRead();
  }
  function fitShown() { if (st.chart && st.mode === "px") st.chart.timeScale().fitContent(); }

  function setMode(mode) {
    st.mode = mode;
    var pxEl = $("mkt-chart"), vsEl = $("mkt-vs"), bP = $("mkt-px-btn"), bV = $("mkt-vs-btn"), lg = $("mkt-legend");
    if (!pxEl || !vsEl) return;
    if (mode === "vs" && st.evaluated) {
      vsEl.style.display = "block"; pxEl.style.display = "none"; if (lg) lg.style.display = "none";
      if (bV) bV.classList.add("on"); if (bP) bP.classList.remove("on");
      drawVs();
    } else {
      vsEl.style.display = "none"; pxEl.style.display = "block"; if (lg) lg.style.display = "";
      if (bP) bP.classList.add("on"); if (bV) bV.classList.remove("on");
      setRead();
      requestAnimationFrame(fitShown);
    }
  }
  function vsPolicy() {
    var sel = $("mkt-sel"), v = sel ? sel.value : "__live__";
    var idx = st.evaluated ? st.evaluated.index : {};
    if (v !== "__live__" && idx[v]) return v;
    if (st.evaluated && idx[st.evaluated.preferred]) return st.evaluated.preferred;
    var k = Object.keys(idx); return k.length ? k[0] : null;
  }
  function drawVs() {
    var el = $("mkt-vs"); if (!el || !st.evaluated) return;
    var p = vsPolicy(); if (!p) return;
    var x = st.evaluated.index[p];
    var rel = x.rel_mean && x.rel_mean.length;
    el.dataset.spec = JSON.stringify(rel ?
      { kind: "index", mean: x.rel_mean, lo: x.rel_lo, hi: x.rel_hi, base: x.rel_mean.map(function () { return 0; }), label: x.label + " against the status quo, %",
        unit: "value weighted index of the eight firms against the status quo on the same path, percent; band 10th to 90th across paths; dashed: no difference", pct: true } :
      { kind: "index", mean: x.mean, lo: x.lo, hi: x.hi, base: x.base, label: x.label,
        unit: "value weighted index, 100 at the announcement; band 10th to 90th across paths; grey: status quo" });
    el.className = "jchart";
    el.style.height = "";
    renderChart(el, true);
    var read = $("mkt-read");
    if (read) {
      var last = x.mean.length - 1;
      read.textContent = x.label + ": " + (x.early * 100).toFixed(1) + "% against the status quo over the first six months, " +
        (x.end * 100).toFixed(1) + "% after " + last + " months; index " + x.mean[last].toFixed(1) + " against " + x.base[last].toFixed(1) + ", means over the paths";
    }
  }

  document.addEventListener("click", function (e) {
    if (e.target.id === "mkt-vs-btn" && !e.target.disabled) setMode("vs");
    if (e.target.id === "mkt-px-btn") setMode("px");
    if (e.target.id === "nws-wire-btn") setNwsMode("wire");
    if (e.target.id === "nws-fc-btn") setNwsMode("fc");
  });
  document.addEventListener("change", function (e) {
    if (e.target.id === "mkt-sel") {
      var v = e.target.value;
      if (v === "__live__") { st.follow = true; if (st.live) show(st.live, true); }
      else { st.follow = false; show(v, true); }
      if (st.mode === "vs") drawVs();
    }
    if (e.target.id === "nws-sel") { st.nwsShown = e.target.value; rebuildWire(); }
  });

  function setRead() {
    var el = $("mkt-read");
    if (!el || st.mode !== "px") return;
    var pol = st.shown ? st.pols[st.shown] : null;
    var n = pol && pol.pts[0] ? pol.pts[0].length : 0;
    el.textContent = (st.shown ? polLabel(st.shown) : "No instrument yet") + (n ? ", " + n + " months, one path shown, 100 at the announcement" : "") +
      (st.follow ? ", following live" : "");
  }

  function syncSelect(name) {
    if (st.selKnown[name]) return;
    st.selKnown[name] = true;
    ["mkt-sel", "nws-sel"].forEach(function (id) {
      var sel = $(id); if (!sel) return;
      var o = document.createElement("option");
      o.value = name; o.textContent = polLabel(name);
      sel.appendChild(o);
    });
  }
  function relabelSelects() {
    ["mkt-sel", "nws-sel"].forEach(function (id) {
      var sel = $(id); if (!sel) return;
      Array.prototype.forEach.call(sel.options, function (o) { if (o.value !== "__live__") o.textContent = polLabel(o.value); });
    });
  }

  /* ------------------------------------------------------ news wire -- */
  function setNwsMode(mode) {
    st.nwsMode = mode;
    var w = $("nws-feed"), f = $("nws-forecast"), bW = $("nws-wire-btn"), bF = $("nws-fc-btn"), sel = $("nws-sel");
    if (!w || !f) return;
    if (mode === "fc") {
      f.style.display = "block"; w.style.display = "none";
      if (bF) bF.classList.add("on"); if (bW) bW.classList.remove("on");
      if (sel) sel.style.visibility = "hidden";
      redrawCharts(true);
    } else {
      f.style.display = "none"; w.style.display = "block";
      if (bW) bW.classList.add("on"); if (bF) bF.classList.remove("on");
      if (sel) sel.style.visibility = "";
    }
  }
  function headRow(host, h, prepend) {
    var row = document.createElement("div");
    var tone = h.tone == null ? 0 : h.tone;
    row.className = "row new " + (tone <= -0.4 ? "neg" : tone >= 0.25 ? "pos" : "neu") + " ty-" + (h.type || "x");
    var t = document.createElement("span"); t.className = "t"; t.textContent = h.date || ""; row.appendChild(t);
    var o = document.createElement("span"); o.className = "o o-" + (h.outlet || "WIRE"); o.textContent = h.outlet || "WIRE"; row.appendChild(o);
    var m = document.createElement("span"); m.className = "m"; m.textContent = h.headline || ""; row.appendChild(m);
    if (h.policy && st.nwsShown === "__live__") { var p = document.createElement("span"); p.className = "pl"; p.textContent = polLabel(h.policy); row.appendChild(p); }
    if (prepend) host.insertBefore(row, host.firstChild); else host.appendChild(row);
    while (host.childNodes.length > 500) host.removeChild(host.lastChild);
  }
  function rebuildWire() {
    var host = $("nws-feed"); if (!host) return;
    host.innerHTML = "";
    var rows = st.heads.filter(function (h) { return st.nwsShown === "__live__" || h.policy === st.nwsShown; });
    rows.slice(-500).forEach(function (h) { headRow(host, h, true); });
    nwsChip();
  }
  function nwsChip() {
    var el = $("nws-live"); if (!el) return;
    if (!st.headCount) { el.textContent = ""; return; }
    el.textContent = st.headCount + " headlines" + (st.lastPressure != null ? " · pressure " + st.lastPressure.toFixed(2) : "") +
      (st.lastTrust != null ? " · trust " + st.lastTrust.toFixed(2) : "") + (st.lastDate ? " · " + st.lastDate : "");
    el.className = "ph-live" + (st.lastPressure != null && st.lastPressure > 0.6 ? " hot" : "");
  }

  /* ------------------------------------------------------ feeds etc -- */
  function feedRow(host, cls, cells, cap) {
    var row = document.createElement("div");
    row.className = "row new " + cls;
    cells.forEach(function (c) {
      var s = document.createElement("span");
      s.className = c[0]; s.textContent = c[1]; row.appendChild(s);
    });
    host.insertBefore(row, host.firstChild);
    while (host.childNodes.length > cap) host.removeChild(host.lastChild);
  }

  function pushTicker(items) {
    st.tickerItems = st.tickerItems.concat(items).slice(-8);
    var el = $("ticker-text");
    if (!el || !st.tickerItems.length) return;
    el.innerHTML = "";
    st.tickerItems.forEach(function (a, i) {
      if (i) { var sep = document.createElement("span"); sep.className = "sep"; sep.textContent = "|"; el.appendChild(sep); }
      var s = document.createElement("span"); s.className = "a-" + a.lvl; s.textContent = a.msg; el.appendChild(s);
    });
  }

  /* -------------------------------------------------- stream fanout -- */
  window.dash_clientside = window.dash_clientside || {};
  window.dash_clientside.psl = {
    onStream: function (d) {
      if (!d) return 0;
      var ready = ensureChart();

      if ((d.run_id && st.runId && d.run_id !== st.runId) || (!d.run_id && st.runId)) {
        /* a new run started: clear the stores */
        st.pols = {}; st.order = []; st.live = null; st.shown = null; st.follow = true; st.heads = [];
        st.evaluated = null; st.selKnown = {}; st.headCount = 0; st.lastDate = null; st.lastPressure = null; st.lastTrust = null;
        DATES = {};
        ["mkt-sel", "nws-sel"].forEach(function (id) {
          var sel = $(id); if (sel) { sel.innerHTML = ""; var o = document.createElement("option"); o.value = "__live__"; o.textContent = "Live"; sel.appendChild(o); }
        });
        st.nwsShown = "__live__";
        st.series.forEach(function (s) { s.setData([]); });
        var bV = $("mkt-vs-btn"); if (bV) bV.disabled = true;
        setMode("px"); setNwsMode("wire");
        var nf = $("nws-feed"); if (nf) nf.innerHTML = "";
        var lf = $("ldg-feed"); if (lf) lf.innerHTML = "";
        st.ledgerCount = 0;
        nwsChip(); setRead();
        var ml = $("mkt-live"); if (ml) ml.textContent = "";
      }
      st.runId = d.run_id || null;

      if (d.pol_labels) { st.polLabels = d.pol_labels; relabelSelects(); }
      if (d.labels && d.labels.length && d.labels.join("|") !== st.labels.join("|")) {
        st.labels = d.labels.slice();
        if (st.chart) buildSeries();
      }

      if (d.ticks && d.ticks.length) {
        d.ticks.forEach(function (t) {
          var name = t.policy;
          if (!st.pols[name]) { st.pols[name] = { pts: st.labels.map(function () { return []; }) }; st.order.push(name); syncSelect(name); }
          var pol = st.pols[name];
          DATES[t.t] = t.date;
          (t.prices || []).forEach(function (v, i) {
            if (!pol.pts[i]) pol.pts[i] = [];
            var arr = pol.pts[i];
            if (!arr.length || arr[arr.length - 1].time < t.t) arr.push({ time: t.t, value: v });
          });
          st.live = name; st.lastDate = t.date; st.lastPressure = t.pressure; st.lastTrust = t.trust;
        });
        if (st.follow && st.live && st.shown !== st.live) show(st.live, true);
        else if (ready && st.shown === st.live) {
          d.ticks.forEach(function (t) {
            if (t.policy !== st.live) return;
            (t.prices || []).forEach(function (v, i) { if (st.series[i]) st.series[i].update({ time: t.t, value: v }); });
          });
          st.chart.timeScale().scrollToRealTime();
        }
        var ml2 = $("mkt-live");
        if (ml2) ml2.textContent = polLabel(st.live) + " · " + (st.lastDate || "");
        setRead();
      }
      if (d.heads && d.heads.length) {
        var host = $("nws-feed");
        d.heads.forEach(function (h) {
          st.heads.push(h); st.headCount += 1;
          if (host && (st.nwsShown === "__live__" || h.policy === st.nwsShown)) headRow(host, h, true);
        });
        if (st.heads.length > 4000) st.heads = st.heads.slice(-4000);
        nwsChip();
      }
      if (d.alerts && d.alerts.length) pushTicker(d.alerts);
      if (d.ledger && d.ledger.length) {
        var lg = $("ldg-feed");
        d.ledger.forEach(function (r) {
          if (lg) feedRow(lg, "info", [["t", "#" + r.seq + " " + r.ts], ["a", r.actor],
            ["m", nice(r.event) + (r.keys ? " (" + r.keys.split(",").map(nice).join(", ").toLowerCase() + ")" : "")], ["h", r.hash + "…"]], 400);
        });
        st.ledgerCount = Math.max(st.ledgerCount, d.ledger[d.ledger.length - 1].seq || 0);
        var pll = $("ph-live-LDG"); if (pll) pll.textContent = "chain " + st.ledgerCount;
      }

      var lamp = $("live-stage");
      if (lamp && d.stage) { lamp.textContent = d.stage.toUpperCase(); lamp.className = "st-" + d.stage; document.body.dataset.stage = d.stage; }
      var ph = $("phase-line"); if (ph && d.phase) ph.textContent = d.phase;
      var pr = $("ph-live-RUN"); if (pr && d.stage) pr.textContent = d.stage;

      if (d.evaluated && !st.evaluated) {
        st.evaluated = d.evaluated;
        var bV2 = $("mkt-vs-btn"); if (bV2) bV2.disabled = false;
        if (!st.follow || true) { /* keep the live view; the official switches to vs baseline by hand */ }
      }
      return 0;
    }
  };

  /* ------------------------------------------------- SVG charts -- */
  var NS = "http://www.w3.org/2000/svg";
  function svgEl(tag, attrs, parent) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) if (attrs.hasOwnProperty(k)) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function text(parent, x, y, s, attrs) {
    var a = { x: x, y: y, fill: TEXT, "font-size": 10, "font-family": "JetBrains Mono, ui-monospace, monospace" };
    for (var k in attrs) a[k] = attrs[k];
    var t = svgEl("text", a, parent); t.textContent = s; return t;
  }
  function fmt(v, nd) {
    if (v == null || isNaN(v)) return "n/a";
    var a = Math.abs(v);
    if (nd == null) nd = a >= 100 ? 0 : a >= 10 ? 1 : a >= 1 ? 1 : 2;
    return (v < 0 ? "-" : "") + a.toFixed(nd).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }
  function clip(s, n) { s = String(s); return s.length > n ? s.slice(0, n - 1) + "…" : s; }
  function niceStep(span, target) {
    var raw = span / Math.max(1, target), p = Math.pow(10, Math.floor(Math.log(raw) / Math.LN10)), r = raw / p;
    return (r <= 1 ? 1 : r <= 2 ? 2 : r <= 5 ? 5 : 10) * p;
  }

  function drawHBars(svg, W, H, spec) {
    var rows = spec.rows || [];
    if (!rows.length) return;
    var labW = Math.min(190, Math.max(90, W * 0.36)), left = labW + 6, right = W - 54, top = spec.unit ? 16 : 4, bottom = H - 16;
    var lo = 0, hi = 0;
    rows.forEach(function (r) { lo = Math.min(lo, r.lo != null ? r.lo : r.value, r.value); hi = Math.max(hi, r.hi != null ? r.hi : r.value, r.value); });
    if (spec.max != null) hi = Math.max(hi, spec.max);
    if (!spec.zero && lo >= 0) lo = 0;
    if (hi === lo) hi = lo + 1;
    var pad = (hi - lo) * 0.04; lo -= lo < 0 ? pad : 0; hi += pad;
    var x = function (v) { return left + (v - lo) / (hi - lo) * (right - left); };
    var rowH = (bottom - top) / rows.length, barH = Math.max(6, Math.min(16, rowH * 0.6));
    var step = niceStep(hi - lo, 5);
    for (var g = Math.ceil(lo / step) * step; g <= hi; g += step) {
      svgEl("line", { x1: x(g), x2: x(g), y1: top, y2: bottom, stroke: GRIDLINE }, svg);
      text(svg, x(g), H - 4, fmt(g, step < 1 ? 2 : 0), { "text-anchor": "middle", fill: MUTED, "font-size": 9 });
    }
    if (lo < 0 && hi > 0) svgEl("line", { x1: x(0), x2: x(0), y1: top, y2: bottom, stroke: HAIR }, svg);
    rows.forEach(function (r, i) {
      var cy = top + rowH * i + rowH / 2;
      text(svg, labW, cy + 3.5, clip(r.label, Math.floor(labW / 6)), { "text-anchor": "end", fill: WHITE });
      var x0 = x(Math.min(0, r.value)), x1 = x(Math.max(0, r.value));
      svgEl("rect", { x: x0, y: cy - barH / 2, width: Math.max(1, x1 - x0), height: barH, fill: r.color || INFO, opacity: 0.85 }, svg);
      if (r.lo != null && r.hi != null) {
        svgEl("line", { x1: x(r.lo), x2: x(r.hi), y1: cy, y2: cy, stroke: WHITE, "stroke-width": 1, opacity: 0.8 }, svg);
        svgEl("line", { x1: x(r.lo), x2: x(r.lo), y1: cy - 4, y2: cy + 4, stroke: WHITE, opacity: 0.8 }, svg);
        svgEl("line", { x1: x(r.hi), x2: x(r.hi), y1: cy - 4, y2: cy + 4, stroke: WHITE, opacity: 0.8 }, svg);
      }
      var vx = (r.hi != null ? Math.max(x(r.hi), x1) : x1) + 4;
      text(svg, Math.min(vx, W - 2), cy + 3.5, spec.max === 1 ? (r.value * 100).toFixed(0) + "%" : fmt(r.value), { fill: WHITE, "font-size": 9 });
    });
    if (spec.unit) text(svg, left, H - 4, "", {});
  }

  function drawWaterfall(svg, W, H, spec) {
    var items = (spec.items || []).slice();
    if (!items.length) return;
    var total = items.reduce(function (s, it) { return s + it.value; }, 0);
    var labW = Math.min(190, Math.max(90, W * 0.36)), left = labW + 6, right = W - 60, top = spec.unit ? 16 : 4, bottom = H - 16;
    var run = 0, lo = 0, hi = 0, segs = [];
    items.forEach(function (it) { var a = run, b = run + it.value; segs.push({ label: it.label, a: a, b: b, v: it.value, kind: it.value >= 0 ? "up" : "down" }); run = b; lo = Math.min(lo, a, b); hi = Math.max(hi, a, b); });
    segs.push({ label: spec.total_label || "Net", a: 0, b: total, v: total, kind: "total" });
    if (hi === lo) hi = lo + 1;
    var pad = (hi - lo) * 0.05; lo -= pad; hi += pad;
    var x = function (v) { return left + (v - lo) / (hi - lo) * (right - left); };
    var rowH = (bottom - top) / segs.length, barH = Math.max(6, Math.min(16, rowH * 0.62));
    var step = niceStep(hi - lo, 5);
    for (var g = Math.ceil(lo / step) * step; g <= hi; g += step) {
      svgEl("line", { x1: x(g), x2: x(g), y1: top, y2: bottom, stroke: GRIDLINE }, svg);
      text(svg, x(g), H - 4, fmt(g, 0), { "text-anchor": "middle", fill: MUTED, "font-size": 9 });
    }
    svgEl("line", { x1: x(0), x2: x(0), y1: top, y2: bottom, stroke: HAIR }, svg);
    segs.forEach(function (s, i) {
      var cy = top + rowH * i + rowH / 2;
      text(svg, labW, cy + 3.5, clip(s.label, Math.floor(labW / 6)), { "text-anchor": "end", fill: s.kind === "total" ? AMBER : WHITE, "font-weight": s.kind === "total" ? 600 : 400 });
      var x0 = x(Math.min(s.a, s.b)), x1 = x(Math.max(s.a, s.b));
      var col = s.kind === "total" ? AMBER : s.kind === "up" ? GOOD : BAD;
      svgEl("rect", { x: x0, y: cy - barH / 2, width: Math.max(1.5, x1 - x0), height: barH, fill: col, opacity: s.kind === "total" ? 0.95 : 0.8 }, svg);
      if (i < segs.length - 2) svgEl("line", { x1: x(s.b), x2: x(s.b), y1: cy + barH / 2, y2: cy + rowH - barH / 2, stroke: HAIR, "stroke-dasharray": "2 2" }, svg);
      var tx = x1 + 4; if (tx > W - 50) tx = x0 - 4;
      text(svg, tx, cy + 3.5, (s.v >= 0 ? "+" : "") + fmt(s.v, 1), { fill: WHITE, "font-size": 9, "text-anchor": tx < x0 ? "end" : "start" });
    });
  }

  function drawLadder(svg, W, H, spec) {
    var L = spec.left || [], R = spec.right || [];
    if (!L.length) return;
    var t0 = spec.unit ? 14 : 0;
    var n = L.length, top = 18 + t0, bottom = H - 6, rowH = (bottom - top) / Math.max(1, n);
    var colW = Math.min(230, (W - 60) / 2), xl = colW, xr = W - colW;
    text(svg, xl, 10 + t0, spec.left_title || "early", { "text-anchor": "end", fill: MUTED, "font-size": 9 });
    text(svg, xr, 10 + t0, spec.right_title || "horizon", { fill: MUTED, "font-size": 9 });
    var posR = {}; R.forEach(function (name, i) { posR[name] = i; });
    L.forEach(function (name, i) {
      var y1 = top + rowH * i + rowH / 2, j = posR[name], y2 = top + rowH * (j == null ? i : j) + rowH / 2;
      var col = j == null || j === i ? MUTED : j < i ? GOOD : BAD;
      svgEl("line", { x1: xl + 8, x2: xr - 8, y1: y1, y2: y2, stroke: col, "stroke-width": j === i ? 1 : 1.5, opacity: 0.85 }, svg);
      svgEl("circle", { cx: xl + 8, cy: y1, r: 2.5, fill: col }, svg);
      svgEl("circle", { cx: xr - 8, cy: y2, r: 2.5, fill: col }, svg);
      text(svg, xl, y1 + 3.5, (i + 1) + "  " + clip(name, Math.floor(colW / 6) - 3), { "text-anchor": "end", fill: WHITE });
    });
    R.forEach(function (name, i) {
      var y = top + rowH * i + rowH / 2;
      var hl = spec.highlight ? name === spec.highlight : i === 0;
      text(svg, xr, y + 3.5, (i + 1) + "  " + clip(name, Math.floor(colW / 6) - 3), { fill: hl ? AMBER : WHITE, "font-weight": hl ? 600 : 400 });
    });
  }

  function drawQuarters(svg, W, H, spec) {
    var bars = spec.bars || [], hiB = spec.hi || [], line = spec.line || [], base = spec.base_bars || [], labels = spec.labels || [];
    if (!bars.length) return;
    var left = 34, right = W - 34, top = spec.unit ? 16 : 6, bottom = H - 16;
    var maxB = 0; bars.forEach(function (v, i) { maxB = Math.max(maxB, v, hiB[i] || 0, base[i] || 0); });
    maxB = maxB || 1;
    var maxL = 0; line.forEach(function (v) { maxL = Math.max(maxL, v); }); maxL = Math.max(maxL, 0.5);
    var n = bars.length, slot = (right - left) / n, bw = Math.max(3, slot * 0.5);
    var yB = function (v) { return bottom - v / (maxB * 1.08) * (bottom - top); };
    var yL = function (v) { return bottom - v / (maxL * 1.08) * (bottom - top); };
    var step = niceStep(maxB, 4);
    for (var g = 0; g <= maxB * 1.05; g += step) {
      svgEl("line", { x1: left, x2: right, y1: yB(g), y2: yB(g), stroke: GRIDLINE }, svg);
      text(svg, left - 4, yB(g) + 3, fmt(g, step < 1 ? 1 : 0), { "text-anchor": "end", fill: MUTED, "font-size": 9 });
    }
    [0, 0.5, 1].forEach(function (f) { var v = maxL * f; text(svg, right + 4, yL(v) + 3, v.toFixed(2), { fill: AMBER, "font-size": 9, opacity: 0.8 }); });
    bars.forEach(function (v, i) {
      var cx = left + slot * i + slot / 2;
      if (base[i] != null) svgEl("rect", { x: cx - bw / 2 - 2, y: yB(base[i]), width: bw + 4, height: Math.max(0, bottom - yB(base[i])), fill: MUTED, opacity: 0.35 }, svg);
      svgEl("rect", { x: cx - bw / 2, y: yB(v), width: bw, height: Math.max(0.5, bottom - yB(v)), fill: BAD, opacity: 0.8 }, svg);
      if (hiB[i] != null) svgEl("line", { x1: cx, x2: cx, y1: yB(v), y2: yB(hiB[i]), stroke: WHITE, opacity: 0.6 }, svg);
      var every = n > 12 ? Math.ceil(n / 10) : 1;
      if (i % every === 0 && labels[i]) text(svg, cx, H - 4, labels[i], { "text-anchor": "middle", fill: MUTED, "font-size": 9 });
    });
    if (line.length) {
      var d = line.map(function (v, i) { return (i ? "L" : "M") + (left + slot * i + slot / 2).toFixed(1) + " " + yL(v).toFixed(1); }).join(" ");
      svgEl("path", { d: d, fill: "none", stroke: AMBER, "stroke-width": 1.5 }, svg);
    }
  }

  function drawTornado(svg, W, H, spec) {
    var rows = (spec.rows || []).slice().sort(function (a, b) { return Math.abs(b.hi - b.lo) - Math.abs(a.hi - a.lo); });
    if (!rows.length) return;
    var ref = spec.ref || 0;
    var labW = Math.min(210, Math.max(100, W * 0.38)), left = labW + 6, right = W - 8, top = spec.unit ? 16 : 4, bottom = H - 16;
    var lo = ref, hi = ref;
    rows.forEach(function (r) { lo = Math.min(lo, r.lo, r.hi); hi = Math.max(hi, r.lo, r.hi); });
    if (hi === lo) hi = lo + 1;
    var pad = (hi - lo) * 0.06; lo -= pad; hi += pad;
    var x = function (v) { return left + (v - lo) / (hi - lo) * (right - left); };
    var rowH = (bottom - top) / rows.length, barH = Math.max(6, Math.min(14, rowH * 0.6));
    var step = niceStep(hi - lo, 5);
    for (var g = Math.ceil(lo / step) * step; g <= hi; g += step) {
      svgEl("line", { x1: x(g), x2: x(g), y1: top, y2: bottom, stroke: GRIDLINE }, svg);
      text(svg, x(g), H - 4, fmt(g, 0), { "text-anchor": "middle", fill: MUTED, "font-size": 9 });
    }
    if (lo < 0 && hi > 0) svgEl("line", { x1: x(0), x2: x(0), y1: top, y2: bottom, stroke: HAIR }, svg);
    svgEl("line", { x1: x(ref), x2: x(ref), y1: top, y2: bottom, stroke: AMBER, "stroke-dasharray": "3 3" }, svg);
    rows.forEach(function (r, i) {
      var cy = top + rowH * i + rowH / 2;
      text(svg, labW, cy + 3.5, clip(r.label, Math.floor(labW / 6)), { "text-anchor": "end", fill: WHITE });
      var a = Math.min(x(r.lo), x(ref)), b = Math.max(x(r.lo), x(ref));
      svgEl("rect", { x: a, y: cy - barH / 2, width: Math.max(1, b - a), height: barH, fill: INFO, opacity: 0.85 }, svg);
      var c = Math.min(x(r.hi), x(ref)), d = Math.max(x(r.hi), x(ref));
      svgEl("rect", { x: c, y: cy - barH / 2, width: Math.max(1, d - c), height: barH, fill: AMBER, opacity: 0.85 }, svg);
      var tl = x(r.lo) < x(r.hi) ? ["lo", "hi"] : ["hi", "lo"];
      var lx = Math.min(x(r.lo), x(r.hi)) - 3, rx = Math.max(x(r.lo), x(r.hi)) + 3;
      var lv = tl[0] === "lo" ? r.lo : r.hi, rv = tl[1] === "lo" ? r.lo : r.hi;
      if (lx > left + 24) text(svg, lx, cy + 3.5, fmt(lv, 0), { "text-anchor": "end", fill: WHITE, "font-size": 9 });
      if (rx < right - 24) text(svg, rx, cy + 3.5, fmt(rv, 0), { fill: WHITE, "font-size": 9 });
    });
  }

  function drawIndex(svg, W, H, spec) {
    var mean = spec.mean || [], lo = spec.lo || mean, hi = spec.hi || mean, base = spec.base || [];
    var n = mean.length; if (!n) return;
    var left = 44, right = W - 10, top = spec.unit ? 18 : 8, bottom = H - 18;
    var ymin = Infinity, ymax = -Infinity;
    [lo, hi, base, mean].forEach(function (arr) { arr.forEach(function (v) { ymin = Math.min(ymin, v); ymax = Math.max(ymax, v); }); });
    if (!isFinite(ymin)) return;
    var pad = (ymax - ymin) * 0.06 || 1; ymin -= pad; ymax += pad;
    var x = function (i) { return left + i / Math.max(1, n - 1) * (right - left); };
    var y = function (v) { return bottom - (v - ymin) / (ymax - ymin) * (bottom - top); };
    var step = niceStep(ymax - ymin, 5);
    for (var g = Math.ceil(ymin / step) * step; g <= ymax + 1e-9; g += step) {
      svgEl("line", { x1: left, x2: right, y1: y(g), y2: y(g), stroke: GRIDLINE }, svg);
      text(svg, left - 4, y(g) + 3, fmt(g, step < 1 ? 1 : 0) + (spec.pct ? "%" : ""), { "text-anchor": "end", fill: MUTED, "font-size": 9 });
    }
    var every = n > 24 ? 12 : 6;
    for (var i = 0; i < n; i += every) {
      svgEl("line", { x1: x(i), x2: x(i), y1: top, y2: bottom, stroke: GRIDLINE }, svg);
      if (DATES[i]) text(svg, x(i), H - 5, DATES[i], { "text-anchor": "middle", fill: MUTED, "font-size": 9 });
      else if (!i) text(svg, x(i), H - 5, "start", { "text-anchor": "middle", fill: MUTED, "font-size": 9 });
    }
    var band = "M" + mean.map(function (_, i) { return x(i).toFixed(1) + " " + y(hi[i]).toFixed(1); }).join(" L") +
               " L" + mean.map(function (_, i) { var j = n - 1 - i; return x(j).toFixed(1) + " " + y(lo[j]).toFixed(1); }).join(" L") + " Z";
    svgEl("path", { d: band, fill: AMBER, opacity: 0.14 }, svg);
    if (base.length) svgEl("path", { d: base.map(function (v, i) { return (i ? "L" : "M") + x(i).toFixed(1) + " " + y(v).toFixed(1); }).join(" "), fill: "none", stroke: TEXT, "stroke-width": 1.2, "stroke-dasharray": "4 3" }, svg);
    svgEl("path", { d: mean.map(function (v, i) { return (i ? "L" : "M") + x(i).toFixed(1) + " " + y(v).toFixed(1); }).join(" "), fill: "none", stroke: AMBER, "stroke-width": 1.8 }, svg);
    var nd = spec.pct ? 1 : 0, suf = spec.pct ? "%" : "";
    text(svg, right, y(mean[n - 1]) - 4, fmt(mean[n - 1], nd) + suf, { "text-anchor": "end", fill: AMBER, "font-size": 9 });
    if (base.length && !spec.pct) text(svg, right, y(base[n - 1]) + 11, fmt(base[n - 1], 0), { "text-anchor": "end", fill: TEXT, "font-size": 9 });
    if (spec.label) text(svg, right - 4, top + 6, spec.label, { "text-anchor": "end", fill: AMBER, "font-size": 10, "font-weight": 600 });
  }

  var DRAW = { hbars: drawHBars, waterfall: drawWaterfall, ladder: drawLadder, quarters: drawQuarters, tornado: drawTornado, index: drawIndex };

  function renderChart(el, force) {
    var spec = el.dataset.spec; if (!spec) return;
    var W = el.clientWidth, H = el.clientHeight;
    if (!W || !H) return;
    var key = spec.length + ":" + W + "x" + H;
    if (!force && el.__key === key) return;
    el.__key = key;
    var data; try { data = JSON.parse(spec); } catch (e) { return; }
    el.innerHTML = "";
    var svg = svgEl("svg", { width: W, height: H, viewBox: "0 0 " + W + " " + H, class: "jsvg" }, el);
    var fn = DRAW[data.kind];
    if (fn) fn(svg, W, H, data);
    if (data.unit) {
      var cap = document.createElement("div"); cap.className = "jcap top"; cap.textContent = data.unit; el.appendChild(cap);
    }
  }
  var chartsPending = false;
  function scheduleCharts() {
    if (chartsPending) return;
    chartsPending = true;
    requestAnimationFrame(function () { chartsPending = false; redrawCharts(false); });
  }
  function redrawCharts(force) {
    document.querySelectorAll(".jchart").forEach(function (el) { renderChart(el, force); });
  }
  window.addEventListener("resize", function () { scheduleCharts(); setTimeout(function () { redrawCharts(true); }, 80); });
  window.pslRedraw = function () { redrawCharts(true); };

  /* ------------------------------------------------------ bootstrap -- */
  function boot() {
    var clockOn = false, chipsOn = false;
    function tryClock() {
      if (clockOn) return true;
      var clk = $("clock"); if (!clk) return false;
      clockOn = true;
      var tick = function () { clk.textContent = new Date().toISOString().slice(11, 19) + " UTC"; };
      tick(); setInterval(tick, 1000);
      return true;
    }
    function tryChips() {
      if (chipsOn) return true;
      var live = { SAF: "harm against the status quo", PNL: "paired with the baseline", WLF: "present values", GAP: "early against horizon",
                   REG: "all runs", RSK: "assurance", POL: "library", DAT: "quarantine", AGT: "archetypes", SEC: "controls" };
      var keys = Object.keys(live);
      if (!$("ph-live-" + keys[0])) return false;
      keys.forEach(function (k) { var el = $("ph-live-" + k); if (el) el.textContent = live[k]; });
      chipsOn = true;
      return true;
    }
    var tries = 0, t = setInterval(function () {
      var up = ensureChart();
      observeBodies();
      scheduleCharts();
      var extras = tryClock() && tryChips();
      if ((up && extras) || ++tries > 240) clearInterval(t);
    }, 250);
    setInterval(function () { observeBodies(); redrawCharts(false); }, 1500);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();

/* ---------------------------------------- ASK: server side, grounded -- */
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var ASK = { welcomed: false, busy: false };
  var esc = function (s) {
    return String(s).replace(/[&<>]/g, function (m) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[m]; });
  };

  function chLog(cls, html) {
    var d = document.createElement("div");
    d.className = "msg " + cls;
    d.innerHTML = html;
    $("ch-log").appendChild(d);
    $("ch-log").scrollTop = 1e9;
    return d;
  }

  function showSources(srcs) {
    $("ch-src").innerHTML = (srcs || []).map(function (c, i) {
      return '<div class="s"><b>[S' + (i + 1) + "] " + esc(c.title) + "</b><br>" + esc(c.text) + "</div>";
    }).join("") || '<div class="s">no matching context</div>';
  }

  function openChat() {
    document.body.classList.add("chatting");
    if (!ASK.welcomed) {
      ASK.welcomed = true;
      chLog("bot", "Ask about this run: which instrument to choose and why, what it costs and who pays, how safe it makes things, " +
        "a firm's stock or the industry's gain or loss, the news to expect, an assumption and whether it changes the answer, " +
        "the red team, the ledger. Answers are computed on the server from the run artefacts; sources appear on the right.");
    }
    var inp = $("ch-in"); if (inp) inp.focus();
  }
  function closeChat() { var i = $("ch-in"); if (i) i.blur(); document.body.classList.remove("chatting"); }

  function clearInput(inp) {
    var set = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
    set.call(inp, "");
    inp.dispatchEvent(new Event("input", { bubbles: true }));
  }

  function askSend() {
    var inp = $("ch-in"), q = (inp.value || "").trim();
    if (!q || ASK.busy) return;
    ASK.busy = true;
    clearInput(inp);
    chLog("user", esc(q));
    var think = chLog("think", "consulting the artefacts …");
    fetch("/ask", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ q: q }) })
      .then(function (r) { return r.json().then(function (d) { d._status = r.status; return d; }); })
      .then(function (d) {
        think.remove();
        if (d.error) { chLog("bot", esc("Not answered: " + d.error)); return; }
        chLog("bot", esc(d.text));
        showSources(d.sources);
        $("ch-brain").textContent = d.brain || "";
      })
      .catch(function (e) { think.remove(); chLog("bot", esc("The server did not answer (" + e + ")")); })
      .then(function () { ASK.busy = false; });
  }

  window.PSL_ASK = { open: openChat, close: closeChat,
    isOpen: function () { return document.body.classList.contains("chatting"); } };

  var tries = 0, t = setInterval(function () {
    var back = $("ch-back"), send = $("ch-send"), inp = $("ch-in");
    if (back && send && inp) {
      back.onclick = closeChat;
      send.onclick = askSend;
      inp.addEventListener("keydown", function (e) { if (e.key === "Enter") { askSend(); e.stopPropagation(); } });
      clearInterval(t);
    } else if (++tries > 240) { clearInterval(t); }
  }, 250);
})();

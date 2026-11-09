/* PSL TERMINAL replay runtime.
   Plays recorded runs back through the terminal's own client code (terminal.js): the stream of ticks,
   headlines, alerts and ledger entries is re emitted in order, and the panels are filled with HTML the
   terminal rendered at each stage when the run was recorded. Nothing here computes a result; the page
   says so. ASK answers in the browser from the recorded artefacts with the same routing as the server. */
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var RAIL = [["plan", "Plan"], ["gate1", "Gate 1"], ["simulate", "Simulate"], ["markets", "Markets"], ["welfare", "Welfare"],
              ["assurance", "Assurance"], ["critic", "Critic"], ["gate2", "Gate 2"], ["released", "Released"]];
  var TICK_MS = 18, STEP_PAUSE = 900, SUB_PAUSE = 220;
  var R = { index: null, run: null, ask: null, stage: "idle", step: "plan", seq: 0, timers: [], playing: false, pick: {} };

  function emit(extra) {
    var d = { seq: ++R.seq, stage: R.stage, phase: extra.phase || null, run_id: R.run ? R.run.run_id : null,
              labels: R.run ? R.run.labels : [], pol_labels: R.run ? R.run.pol_labels : {}, policy: null,
              ticks: [], heads: [], alerts: [], ledger: [], done: [] };
    for (var k in extra) if (extra.hasOwnProperty(k)) d[k] = extra[k];
    if (!d.phase) delete d.phase;
    window.dash_clientside.psl.onStream(d);
  }
  function setBody(id, html) { var el = $(id); if (el) { el.innerHTML = html; } }
  function frag(name) { return (R.run && R.run.fragments[name]) || ""; }
  function setRail() {
    var rail = $("rail"); if (!rail) return;
    var order = RAIL.map(function (r) { return r[0]; }), cur = Math.max(0, order.indexOf(R.step));
    rail.innerHTML = "";
    RAIL.forEach(function (r, i) {
      var cls = "rail-step";
      if (R.stage === "idle") { /* nothing lit */ }
      else if (R.stage === "released") cls += r[0] === "released" ? " ok" : " done";
      else if (i < cur) cls += " done";
      else if (i === cur) cls += (["error", "halted", "rejected", "refused"].indexOf(R.stage) >= 0) ? " fail" : " active";
      var s = document.createElement("span"); s.className = cls; s.dataset.step = r[0]; s.textContent = r[1]; rail.appendChild(s);
    });
  }
  function setButtons() {
    var st = R.stage, busy = R.playing;
    var dis = function (id, v) { var b = $(id); if (b) b.disabled = !!v; };
    dis("plan", st === "planning" || st === "running" || busy);
    dis("stop", !(st === "planning" || st === "running"));
    dis("g1a", st !== "planned"); dis("g1r", st !== "planned");
    dis("g2a", st !== "evaluated"); dis("g2r", st !== "evaluated");
    var sel = $("rec-sel"); if (sel) sel.disabled = (st !== "idle");
  }
  function setStage(stage, step, phase) {
    R.stage = stage; if (step) R.step = step;
    setRail(); setButtons();
    var chip = $("run-chip"); if (chip) chip.textContent = R.run && stage !== "idle" ? "run " + R.run.run_id + " (replay)" : "";
    var v = $("ldg-verify"); if (v && R.run) v.textContent = R.run.verify[stage] || v.textContent;
    emit({ phase: phase || undefined });
  }
  function clearTimers() { R.timers.forEach(clearTimeout); R.timers = []; R.playing = false; }
  function later(fn, ms) { var t = setTimeout(fn, ms); R.timers.push(t); return t; }

  /* ----------------------------------------------------------- stages -- */
  function showIdle() {
    setBody("run-status", R.index.shared.run_idle || "");
    setBody("saf-body", frag("await_saf")); setBody("pnl-body", frag("await_pnl")); setBody("wlf-body", frag("await_wlf"));
    setBody("gap-body", frag("await_gap")); setBody("nws-forecast", frag("await_nws_fc")); setBody("rsk-body", frag("await_rsk"));
    var v = $("ldg-verify"); if (v) v.textContent = "No run open";
    var ph = $("phase-line"); if (ph) ph.textContent = "Awaiting run control (replay)";
    window.pslRedraw && window.pslRedraw();
  }
  function eventsBetween(a, b) {
    return R.run.events.filter(function (e) { return e.seq > a && e.seq <= b; });
  }
  function emitPlain(evs) {
    // alerts and ledger rows outside the live run, emitted at once
    var alerts = [], ledger = [];
    evs.forEach(function (e) {
      if (e.kind === "alert") alerts.push({ t: e.t, lvl: e.lvl, msg: e.msg });
      if (e.kind === "ledger") ledger.push(e.row);
    });
    if (alerts.length || ledger.length) emit({ alerts: alerts, ledger: ledger });
  }

  function plan() {
    if (!R.run || R.stage !== "idle") return;
    fill("who", "Developer1"); fill("who-role", "Developer1"); fill("approver", "Developer2"); fill("approver-role", "Developer2");
    R.playing = true;
    setStage("planning", "plan", "Reading the question and planning the battery (replay)");
    later(function () {
      emitPlain(eventsBetween(0, R.run.marks.planned));
      R.playing = false;
      setBody("run-status", frag("run_planned"));
      setStage("planned", "gate1", "Battery planned, awaiting Gate 1 (replay of run " + R.run.run_id + ")");
    }, 900);
  }
  function gate1() {
    if (R.stage !== "planned") return;
    emitPlain(eventsBetween(R.run.marks.planned, R.run.marks.running));
    setBody("run-status", frag("run_running"));
    setStage("running", "simulate", "Gate 1 approved, battery running (replay)");
    R.playing = true;
    play(eventsBetween(R.run.marks.running, R.run.marks.evaluated), 0);
  }
  function play(evs, i) {
    if (!R.playing) return;
    if (i >= evs.length) { finishRun(); return; }
    var e = evs[i], j = i + 1, delay = 0;
    if (e.kind === "tick") {
      var heads = [];
      while (j < evs.length && evs[j].kind === "head") { heads.push(stripSeq(evs[j])); j++; }
      emit({ ticks: [stripSeq(e)], heads: heads, policy: e.policy });
      delay = TICK_MS;
    } else if (e.kind === "phase") {
      R.step = e.step; setRail();
      emit({ phase: e.phase, policy: e.policy || null });
      delay = (e.step === "simulate") ? 350 : (e.phase.indexOf(":") >= 0 ? SUB_PAUSE : STEP_PAUSE);
    } else if (e.kind === "alert") {
      emit({ alerts: [{ t: e.t, lvl: e.lvl, msg: e.msg }] });
    } else if (e.kind === "ledger") {
      emit({ ledger: [e.row] });
    } else if (e.kind === "head") {
      emit({ heads: [stripSeq(e)] });
    }
    later(function () { play(evs, j); }, delay);
  }
  function stripSeq(e) { var o = {}; for (var k in e) if (k !== "seq" && k !== "kind") o[k] = e[k]; return o; }
  function finishRun() {
    R.playing = false;
    R.pick = { pnl: R.run.preferred, wlf: R.run.preferred, nws: R.run.preferred };
    setBody("saf-body", frag("saf")); setBody("gap-body", frag("gap")); setBody("rsk-body", frag("rsk"));
    setBody("pnl-body", frag("pnl_" + R.pick.pnl)); setBody("wlf-body", frag("wlf_" + R.pick.wlf)); setBody("nws-forecast", frag("nws_fc_" + R.pick.nws));
    setBody("run-status", frag("run_evaluated"));
    setStage("evaluated", "gate2", "Critic passed, Gate 2 armed, preferred " + R.run.pol_labels[R.run.preferred] + " (replay)");
    emit({ evaluated: R.run.evaluated });
    window.pslRedraw && window.pslRedraw();
  }
  function gate2() {
    if (R.stage !== "evaluated") return;
    emitPlain(eventsBetween(R.run.marks.evaluated, R.run.marks.released));
    setBody("run-status", frag("run_released"));
    setStage("released", "released", "Briefing released, evidence pack built (replay)");
    window.pslRedraw && window.pslRedraw();
  }
  function refuse(which) {
    var reason = ($("reason") && $("reason").value || "").trim();
    if (!reason) { emit({ alerts: [{ t: now(), lvl: "alert", msg: "Refusing a gate needs a reason" }] }); return; }
    var stage = which === 1 ? "rejected" : "refused";
    var host = $("run-status");
    if (host) {
      var d = document.createElement("div"); d.className = "seal refused";
      d.textContent = (which === 1 ? "Gate 1" : "Gate 2") + " refused in the replay by " + (($("approver") || {}).value || "the approver") + ": " + reason +
        ". The recorded run is left as it was; the live terminal records a refusal in the ledger and seals the run.";
      host.appendChild(d);
    }
    setStage(stage, which === 1 ? "gate1" : "gate2", (which === 1 ? "Gate 1 refused, battery not run" : "Gate 2 refused, briefing withheld") + " (replay)");
    emit({ alerts: [{ t: now(), lvl: "alert", msg: (which === 1 ? "Gate 1" : "Gate 2") + " refused: " + reason }] });
  }
  function stop() {
    if (R.stage !== "running") return;
    clearTimers();
    var host = $("run-status");
    if (host) { var d = document.createElement("div"); d.className = "seal"; d.textContent = "Emergency stop in the replay: playback halted. New run clears the terminal."; host.appendChild(d); }
    setStage("halted", R.step, "Emergency stop, playback halted (replay)");
    emit({ alerts: [{ t: now(), lvl: "alert", msg: "Emergency stop requested; playback halted" }] });
  }
  function newRun() {
    clearTimers();
    R.stage = "idle"; R.step = "plan";
    emit({ run_id: null, phase: "Awaiting run control (replay)" });   // a null run id clears the client stores
    R.run = R.run;   // keep the selected recording
    setStage("idle", "plan", "Awaiting run control (replay)");
    showIdle();
    emit({ alerts: [{ t: now(), lvl: "info", msg: "New run: the terminal is clear. Choose a recorded question and plan the battery." }] });
  }
  function now() { return new Date().toISOString().slice(11, 19); }
  function fill(id, v) {
    var el = $(id); if (!el) return;
    var set = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
    try { set.call(el, v); } catch (e) { el.value = v; }
    el.dispatchEvent(new Event("input", { bubbles: true }));
  }

  /* ---------------------------------------------------------- recorded -- */
  function loadRun(rid, then) {
    fetch("data/" + rid + "/replay.json").then(function (r) { return r.json(); }).then(function (run) {
      R.run = run; R.ask = null;
      fetch("data/" + rid + "/ask.json").then(function (r) { return r.json(); }).then(function (a) { R.ask = a; });
      var q = $("q");
      if (q) { q.value = run.question; q.readOnly = true; q.title = "The question of the recorded run; change the recording above, or ask the live terminal"; }
      emit({ run_id: null });
      R.stage = "idle"; R.step = "plan";
      showIdle(); setRail(); setButtons();
      if (then) then();
    });
  }
  function buildSelector() {
    var body = $("body-RUN"); if (!body) return;
    var wrap = document.createElement("div"); wrap.className = "rec-wrap";
    var lab = document.createElement("label"); lab.htmlFor = "rec-sel"; lab.textContent = "Recorded question (replay)";
    var sel = document.createElement("select"); sel.id = "rec-sel"; sel.className = "sel";
    R.index.runs.forEach(function (r, i) {
      var o = document.createElement("option"); o.value = r.run_id;
      o.textContent = (i + 1) + ". " + r.question.slice(0, 110) + (r.question.length > 110 ? "…" : "");
      sel.appendChild(o);
    });
    sel.addEventListener("change", function () { if (R.stage === "idle") loadRun(sel.value); });
    wrap.appendChild(lab); wrap.appendChild(sel);
    body.insertBefore(wrap, body.firstChild);
  }

  /* ------------------------------------------------------------- ASK -- */
  function tok(s) { var m = s.toLowerCase().match(/[a-z][a-z0-9]+/g) || []; return new Set(m); }
  function answer(q) {
    var A = R.ask;
    if (!A || !R.run || ["evaluated", "released", "refused"].indexOf(R.stage) < 0) {
      return { text: "No run has been evaluated yet in this replay. Plan the battery and approve it at Gate 1.", sources: [], intent: "none" };
    }
    var by = {}; A.chunks.forEach(function (c) { by[c.id] = c; });
    var ql = q.toLowerCase(), i, p, srcs;
    for (i = 0; i < A.policies.length; i++) {
      p = A.policies[i];
      if (ql.indexOf(p.name.replace(/_/g, " ")) >= 0 || ql.indexOf(p.label.toLowerCase()) >= 0 || ql.indexOf(p.name) >= 0) {
        srcs = [by["pol_" + p.name]];
        if (/market|stock|share/.test(ql)) srcs.push(by["market_" + p.name] || by["market"]);
        srcs = srcs.filter(Boolean);
        return { text: srcs.map(function (s) { return s.text; }).join(" "), sources: srcs, intent: "policy" };
      }
    }
    for (i = 0; i < A.firms.length; i++) {
      var f = A.firms[i];
      if (ql.indexOf(f.label.toLowerCase()) >= 0 || ql.indexOf(f.name.replace(/_/g, " ")) >= 0) {
        return { text: f.text, sources: [by["market"], by["firms"]].filter(Boolean), intent: "firm" };
      }
    }
    var qt = tok(ql), qa = Array.from(qt);
    for (i = 0; i < A.assumptions.length; i++) {
      var a = A.assumptions[i];
      var hit = a.words.filter(function (w) { return qt.has(w) || qa.some(function (t) { return t.indexOf(w.slice(0, 6)) === 0; }); }).length;
      if (ql.indexOf(a.nice) >= 0 || ql.indexOf(a.key) >= 0 || (a.words.length && hit >= Math.min(2, a.words.length))) {
        return { text: a.text, sources: [by["assumptions"], by["tornado"]].filter(Boolean), intent: "assumption" };
      }
    }
    var best = "answer", score = 0;
    A.intents.forEach(function (it) {
      var w = A.weak[it[0]] || 1, hits = it[1].filter(function (k) { return ql.indexOf(k) >= 0; }).length * w;
      if (hits > score) { best = it[0]; score = hits; }
    });
    if (best === "preferred") {
      srcs = [by["pol_" + A.preferred], by["distribution"]].filter(Boolean);
      return { text: srcs.map(function (s) { return s.text; }).join(" "), sources: srcs, intent: best };
    }
    if (by[best]) {
      srcs = [by[best]];
      if (best === "answer") srcs = srcs.concat([by["constraints"], by["gap"]].filter(Boolean));
      return { text: srcs.map(function (s) { return s.text; }).join(" "), sources: srcs, intent: best };
    }
    var scored = A.chunks.map(function (c) {
      var ct = tok(c.title + " " + c.text), overlap = 0;
      qt.forEach(function (t) { if (ct.has(t)) overlap++; });
      var bonus = qa.some(function (w) { return c.title.toLowerCase().indexOf(w) >= 0; }) ? 3 : 0;
      return [overlap + bonus, c];
    }).sort(function (x, y) { return y[0] - x[0]; });
    var top = scored.slice(0, 3).filter(function (x) { return x[0] > 0; }).map(function (x) { return x[1]; });
    srcs = top.length ? top : A.chunks.slice(0, 3);
    return { text: srcs.map(function (s) { return s.text; }).join(" "), sources: srcs, intent: "retrieve" };
  }
  var realFetch = window.fetch.bind(window);
  window.fetch = function (url, opts) {
    if (typeof url === "string" && url === "/ask") {
      var q = "";
      try { q = JSON.parse(opts.body).q || ""; } catch (e) { /* ignore */ }
      var a = answer(q);
      var body = JSON.stringify({ text: a.text, sources: a.sources.map(function (s) { return { id: s.id, title: s.title, text: s.text.slice(0, 420) + (s.text.length > 420 ? "…" : "") }; }),
                                  brain: "replay: computed in the browser from the recorded artefacts", intent: a.intent });
      return Promise.resolve(new Response(body, { status: 200, headers: { "Content-Type": "application/json" } }));
    }
    return realFetch(url, opts);
  };

  /* ------------------------------------------------------------ wiring -- */
  document.addEventListener("click", function (e) {
    var t = e.target.closest ? e.target.closest("button, .dat-upload") : null;
    if (!t) return;
    switch (t.id) {
      case "plan": plan(); break;
      case "g1a": gate1(); break;
      case "g1r": refuse(1); break;
      case "g2a": gate2(); break;
      case "g2r": refuse(2); break;
      case "stop": stop(); break;
      case "newrun": newRun(); break;
      case "sec-recheck": setBody("sec-body", R.index.shared.sec); break;
      case "pol-add": case "pol-on": case "pol-off": case "pol-remove": case "pol-template": case "asm-apply":
        setBody(t.id === "asm-apply" ? "asm-result" : "pol-result", '<div class="seal">Not available in the replay: instruments and assumption overrides are stored on the live terminal.</div>'); break;
      case "agt-add": case "agt-on": case "agt-off": case "agt-remove": case "agt-template":
        setBody("agt-result", '<div class="seal">Not available in the replay: firm templates are stored on the live terminal.</div>'); break;
      default:
        if (t.classList.contains("dat-upload")) setBody("dat-result", '<div class="seal">Uploads are not available in the replay; the live terminal takes a price series through quarantine.</div>');
    }
  });
  document.addEventListener("change", function (e) {
    var t = e.target;
    if (!t || t.type !== "radio") return;
    var map = { "pnl-pick": ["pnl", "pnl-body", "pnl_"], "wlf-pick": ["wlf", "wlf-body", "wlf_"], "nws-pick": ["nws", "nws-forecast", "nws_fc_"] };
    var m = map[t.name]; if (!m || !R.run) return;
    R.pick[m[0]] = t.value;
    setBody(m[1], frag(m[2] + t.value));
    window.pslRedraw && window.pslRedraw();
  });

  function boot() {
    fetch("data/index.json").then(function (r) { return r.json(); }).then(function (idx) {
      R.index = idx;
      setBody("sec-body", idx.shared.sec); setBody("reg-body", idx.shared.reg);
      setBody("pol-list", idx.shared.pol_list); setBody("agt-list", idx.shared.agt_list); setBody("dat-list", idx.shared.dat_list);
      buildSelector();
      if (idx.runs.length) loadRun(idx.runs[0].run_id);
      var brain = $("ch-brain"); if (brain) brain.textContent = "replay: answers computed in the browser from the recorded artefacts";
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();

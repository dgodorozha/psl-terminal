"""Browser check of the static replay site: serve the folder, walk the replay through plan, Gate 1, playback,
Gate 2, every page and ASK, take screenshots and fail on any browser console error.

    python tools/test_static.py site shots_static
"""

import http.server
import os
import socketserver
import sys
import threading
import time

from playwright.sync_api import sync_playwright

SITE = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "site")
OUT = sys.argv[2] if len(sys.argv) > 2 else "shots_static"
PORT = 8765
os.makedirs(OUT, exist_ok=True)


class Quiet(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=SITE, **k)

    def log_message(self, *a):
        pass


srv = socketserver.TCPServer(("127.0.0.1", PORT), Quiet)
threading.Thread(target=srv.serve_forever, daemon=True).start()
errors = []


def shot(page, name):
    page.screenshot(path=os.path.join(OUT, name + ".png"))
    print("shot", name, flush=True)


def wait_stage(page, stages, timeout=120):
    t0 = time.time()
    while time.time() - t0 < timeout:
        st = page.evaluate("document.body.dataset.stage || ''")
        if st in stages:
            return st
        time.sleep(0.3)
    raise SystemExit(f"timed out waiting for {stages}; stage {page.evaluate('document.body.dataset.stage')}")


with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1600, "height": 940}, device_scale_factor=2)
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(f"http://127.0.0.1:{PORT}/index.html")
    page.wait_for_selector("#rec-sel", timeout=30000)
    time.sleep(1.5)
    shot(page, "00_front")
    page.keyboard.press("Enter"); time.sleep(0.8)
    shot(page, "01_grid_idle")
    page.keyboard.press("k"); time.sleep(0.4)
    assert page.evaluate("document.body.classList.contains('hasmax')")
    page.click("button.fkey[data-code='REG']"); time.sleep(0.5); shot(page, "02_reg")
    page.click("button.fkey[data-code='SEC']"); time.sleep(0.5); shot(page, "03_sec")
    page.keyboard.press("Escape"); time.sleep(0.3)
    page.keyboard.press("8"); time.sleep(0.5)
    shot(page, "10_run_idle")
    page.click("#plan")
    wait_stage(page, {"planned"}, 20)
    time.sleep(0.6); shot(page, "11_planned")
    page.click("#g1a")
    wait_stage(page, {"running"}, 10)
    time.sleep(4)
    page.keyboard.press("Escape"); time.sleep(0.5); shot(page, "12_running_grid")
    wait_stage(page, {"evaluated"}, 120)
    time.sleep(1.5); shot(page, "20_evaluated_grid")
    for key, name in (("3", "21_saf"), ("4", "22_pnl"), ("5", "23_wlf"), ("6", "24_gap"), ("k", "25_rsk"), ("7", "26_ldg")):
        page.keyboard.press(key); time.sleep(0.9); shot(page, name)
    # instrument picker swaps the fragment
    page.keyboard.press("4"); time.sleep(0.4)
    labels = page.query_selector_all("#pnl-pick label")
    assert len(labels) >= 2
    labels[1].click(); time.sleep(0.6)
    assert page.evaluate("document.querySelectorAll('#pnl-pick input:checked').length") == 1
    shot(page, "22b_pnl_pick")
    page.keyboard.press("1"); time.sleep(0.4); page.click("#nws-fc-btn"); time.sleep(0.8); shot(page, "27_nws_forecast")
    page.keyboard.press("2"); time.sleep(0.4); page.click("#mkt-vs-btn"); time.sleep(0.8); shot(page, "28_mkt_vs")
    page.keyboard.press("Escape")
    page.keyboard.press("9"); time.sleep(0.5)
    page.fill("#ch-in", "which instrument should we choose and why?"); page.keyboard.press("Enter"); time.sleep(1.0)
    txt = page.inner_text("#ch-log")
    assert "Preferred" in txt or "preferred" in txt, txt[:300]
    shot(page, "30_ask")
    page.keyboard.press("Escape")
    page.keyboard.press("8"); time.sleep(0.4)
    page.click("#g2a")
    wait_stage(page, {"released"}, 10)
    time.sleep(1.0); shot(page, "40_released")
    page.keyboard.press("Escape"); time.sleep(0.4); shot(page, "41_grid_released")
    page.keyboard.press("8"); time.sleep(0.3)
    page.click("#newrun"); time.sleep(1.0)
    assert page.evaluate("document.body.dataset.stage") == "idle"
    # second recording
    page.select_option("#rec-sel", index=1); time.sleep(1.0)
    page.click("#plan"); wait_stage(page, {"planned"}, 20)
    page.click("#g1a"); wait_stage(page, {"running"}, 10)
    wait_stage(page, {"evaluated"}, 120)
    time.sleep(1.0); page.keyboard.press("Escape"); time.sleep(0.6); shot(page, "50_second_run")
    b.close()
srv.shutdown()
bad = [e for e in errors if "favicon" not in e]
if bad:
    print("BROWSER ERRORS:\n" + "\n".join(bad[:20]))
    sys.exit(1)
print("static replay ok, no browser errors")

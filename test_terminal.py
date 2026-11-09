"""Browser walkthrough of the PSL terminal with Playwright: front page, plan,
Gate 1, the live run, Gate 2, every page, ASK. Writes screenshots to
shots/ and fails on any browser console error.

    PSL_SECRET=testkey PSL_DEV_MODE=on PSL_PROFILE=demo PSL_REGISTER=sample_data/register.csv python dash_app.py &
    python test_terminal.py http://127.0.0.1:8070
"""

import os
import sys
import time

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8070"
OUT = sys.argv[2] if len(sys.argv) > 2 else "shots"
os.makedirs(OUT, exist_ok=True)
errors = []


def shot(page, name):
    page.screenshot(path=os.path.join(OUT, name + ".png"))
    print("shot", name, flush=True)


def wait_stage(page, stages, timeout=240):
    t0 = time.time()
    while time.time() - t0 < timeout:
        st = page.evaluate("document.body.dataset.stage || ''")
        if st in stages:
            return st
        time.sleep(0.5)
    raise SystemExit(f"timed out waiting for {stages}, stage is {page.evaluate('document.body.dataset.stage')}")


def set_value(page, selector, value):
    page.fill(selector, "")
    page.fill(selector, value)


with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1600, "height": 940}, device_scale_factor=2)
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(BASE)
    page.wait_for_selector("#front", timeout=30000)
    time.sleep(1.5)
    shot(page, "00_front")
    page.keyboard.press("Enter")
    time.sleep(1.0)
    shot(page, "01_grid_idle")

    # keyboard and footer navigation from anywhere
    page.keyboard.press("k"); time.sleep(0.4)
    assert page.evaluate("document.body.classList.contains('hasmax')"), "K should maximise RSK"
    shot(page, "02_rsk_idle")
    page.click("button.fkey[data-code='POL']"); time.sleep(0.6)
    assert page.evaluate("document.querySelector('#panel-POL').classList.contains('maxed')"), "footer key POL from RSK"
    page.click("#pol-add"); time.sleep(1.0)
    assert "Stored" in page.inner_text("#pol-result"), page.inner_text("#pol-result")
    shot(page, "03_pol")
    page.click("#pol-pick label"); time.sleep(0.4)
    page.click("#pol-remove"); time.sleep(0.8)
    assert "Removed" in page.inner_text("#pol-result"), page.inner_text("#pol-result")
    page.click("button.fkey[data-code='AGT']"); time.sleep(0.5); shot(page, "04_agt")
    page.click("button.fkey[data-code='DAT']"); time.sleep(0.5)
    page.fill("#dat-event", "2024-06")
    page.fill("#dat-maps", "chip_designer")
    page.set_input_files("#dat-upload input[type=file]", os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_data", "analogue_event_study.csv"))
    page.wait_for_selector("#dat-result .seal.approved", timeout=20000)
    time.sleep(0.8); shot(page, "05_dat")
    page.set_input_files("#dat-upload input[type=file]", os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_data", "refused_pii_example.csv"))
    page.wait_for_selector("#dat-result .seal.refused", timeout=20000)
    assert "personal identifiers" in page.inner_text("#dat-result")
    time.sleep(0.5); shot(page, "05b_dat_refused")
    page.click("button.fkey[data-code='SEC']"); time.sleep(0.8); shot(page, "06_sec")
    page.keyboard.press("Escape"); time.sleep(0.4)

    # RUN: plan with Developer1 / Developer2
    page.keyboard.press("8"); time.sleep(0.5)
    set_value(page, "#who", "Developer1")
    set_value(page, "#who-role", "Developer1")
    set_value(page, "#approver", "Developer2")
    set_value(page, "#approver-role", "Developer2")
    page.click("#plan")
    wait_stage(page, {"planned"}, 60)
    time.sleep(1.5)
    shot(page, "10_planned")
    page.click("#g1a")
    wait_stage(page, {"running"}, 30)
    time.sleep(6)
    page.keyboard.press("Escape"); time.sleep(0.6)
    shot(page, "11_running_grid")
    page.keyboard.press("1"); time.sleep(0.8); shot(page, "12_nws_live")
    page.keyboard.press("2"); time.sleep(0.8); shot(page, "13_mkt_live")
    page.keyboard.press("Escape")
    wait_stage(page, {"evaluated", "error", "halted"}, 400)
    st = page.evaluate("document.body.dataset.stage")
    assert st == "evaluated", f"run ended in {st}"
    time.sleep(3)
    shot(page, "20_evaluated_grid")
    for key, name in (("3", "21_saf"), ("4", "22_pnl"), ("5", "23_wlf"), ("6", "24_gap"), ("k", "25_rsk"), ("7", "26_ldg")):
        page.keyboard.press(key); time.sleep(1.2); shot(page, name)
    page.keyboard.press("1"); time.sleep(0.5)
    page.click("#nws-fc-btn"); time.sleep(1.0); shot(page, "27_nws_forecast")
    page.keyboard.press("2"); time.sleep(0.5)
    page.click("#mkt-vs-btn"); time.sleep(1.0); shot(page, "28_mkt_vs")
    page.keyboard.press("Escape")

    # ASK
    page.keyboard.press("9"); time.sleep(0.6)
    page.fill("#ch-in", "which instrument should we choose and why?")
    page.keyboard.press("Enter"); time.sleep(2.5)
    shot(page, "30_ask")
    page.keyboard.press("Escape")

    # Gate 2
    page.keyboard.press("8"); time.sleep(0.5)
    page.click("#g2a")
    wait_stage(page, {"released"}, 90)
    time.sleep(2.5)
    shot(page, "40_released")
    page.keyboard.press("Escape"); time.sleep(0.5)
    page.keyboard.press("r"); time.sleep(1.0); shot(page, "41_reg")
    page.keyboard.press("Escape"); time.sleep(0.5)
    shot(page, "42_grid_released")

    # New run clears the terminal
    page.keyboard.press("8"); time.sleep(0.4)
    page.click("#newrun"); time.sleep(3)
    st = page.evaluate("document.body.dataset.stage")
    assert st == "idle", f"new run should return to idle, got {st}"
    shot(page, "50_newrun")
    b.close()

bad = [e for e in errors if "favicon" not in e and "404" not in e]
if bad:
    print("BROWSER ERRORS:\n" + "\n".join(bad[:20]))
    sys.exit(1)
print("walkthrough ok, no browser errors")

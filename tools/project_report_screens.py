"""Screenshots of the HTML pages the project generates, for the project report.

    .venv/Scripts/python.exe re-peat/tools/project_report_screens.py [--only <name> ...]

Serves the workspace on a local port (the twin and the SiTMAT dashboard use ES modules or fetch, which need http) and
captures each page in PAGES with Playwright driving the installed Chrome (CHROME, or its default Windows path) into
re-peat/reports/project_report/figures/screen_<name>.png. Basemaps and CDN libraries need internet. Pages are given
time to render after the network is idle; a page whose data file is missing is skipped with a message.
"""
from __future__ import annotations

import argparse
import functools
import http.server
import os
import threading
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]
OUT = WORKSPACE / "re-peat/reports/project_report/figures"
CHROME = os.environ.get("CHROME", r"C:\Program Files\Google\Chrome\Application\chrome.exe")
PORT = 8766

# name: (path relative to the workspace, query, width, height, wait ms)
PAGES = {
    "national_dashboard": ("re-peat/reports/national_profile/dashboard.html", "", 1440, 1500, 8000),
    "national_dashboard_full": ("re-peat/reports/national_profile/dashboard.html", "", 1440, 4200, 8000),
    "dem_benchmark": ("re-peat/reports/dem_benchmark/report.html", "", 1280, 2000, 2000),
    "dmpg": ("re-peat/reports/investigations/dmpg/dmpg.html", "", 1440, 1400, 8000),
    "sitmat": ("repeat-sitmat/index.html", "", 1440, 1000, 8000),
    "twin": ("repeat-vis/index.html", "?khg=16.02.01&lang=en", 1440, 900, 10000),
    "interventions_report": ("_khg/16.02.01_sugihan_lumpur/05_pump/lidar/report.html", "", 1280, 2400, 8000),
    "interventions_user_guide": ("repeat-pump/docs/user_guide.html", "", 1280, 1600, 2000),
    "interventions_wizard": ("repeat-pump/docs/wizard.html", "", 1280, 1100, 2000),
}


def serve():
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(WORKSPACE))
    h.log_message = lambda *a, **k: None
    s = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), h)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


def shoot(page, name, rel, query, w, h, wait):
    if not (WORKSPACE / rel).exists():
        print(f"skip {name}: {rel} not found")
        return
    out = OUT / f"screen_{name}.png"
    page.set_viewport_size({"width": w, "height": h})
    page.goto(f"http://127.0.0.1:{PORT}/{rel}{query}", wait_until="networkidle", timeout=120000)
    page.wait_for_timeout(wait)                      # maps and charts draw after the data and tiles arrive
    page.screenshot(path=str(out), full_page=False)
    print(f"{name}: {out.name}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright
    s = serve()
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch(executable_path=CHROME, args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
            page = b.new_page(device_scale_factor=1.5)
            for name, spec in PAGES.items():
                if not a.only or name in a.only:
                    shoot(page, name, *spec)
            b.close()
    finally:
        s.shutdown()


if __name__ == "__main__":
    main()

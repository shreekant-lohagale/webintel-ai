"""Read-only multi-viewport smoke check for a running WebIntel frontend."""

import json
import os
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright


BASE_URL = os.getenv("WEBINTEL_SMOKE_URL", "http://127.0.0.1:5173/")
ROUTES = tuple(filter(None, os.getenv("WEBINTEL_SMOKE_ROUTES", "/,/documents,/search,/assistant,/topics,/monitoring,/settings").split(",")))
WIDTHS = tuple(int(value) for value in os.getenv("WEBINTEL_SMOKE_WIDTHS", "375,768,1024,1440").split(","))


def main() -> None:
    results: list[dict] = []
    failed = False
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        routes = list(ROUTES)
        if "/documents" in routes:
            discovery = browser.new_page(viewport={"width": 1440, "height": 900})
            discovery.goto(urljoin(BASE_URL, "documents"), wait_until="domcontentloaded")
            discovery.wait_for_timeout(1_500)
            detail_links = discovery.locator('a[href^="/documents/"]')
            if detail_links.count():
                detail_route = detail_links.first.get_attribute("href")
                if detail_route and detail_route not in routes:
                    routes.append(detail_route)
            discovery.close()
        for width in WIDTHS:
            for route in routes:
                page = browser.new_page(viewport={"width": width, "height": 900})
                console_errors: list[str] = []
                page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
                page.on("pageerror", lambda error: console_errors.append(str(error)))
                response = page.goto(urljoin(BASE_URL, route.lstrip("/")), wait_until="domcontentloaded")
                page.wait_for_timeout(1_500)
                metrics = page.evaluate("""() => ({
                  overflow: document.documentElement.scrollWidth > window.innerWidth + 1,
                  overflowElements: [...document.querySelectorAll('body *')]
                    .filter((element) => !element.closest('.overflow-x-auto') && element.getBoundingClientRect().right > window.innerWidth + 1)
                    .slice(0, 5)
                    .map((element) => ({ tag: element.tagName, className: String(element.className), right: Math.round(element.getBoundingClientRect().right) })),
                  h1: document.querySelectorAll('h1').length,
                  title: document.title
                })""")
                if width == 375 and route == "/":
                    page.get_by_role("button", name="Open navigation").click()
                    metrics["mobile_dialog"] = page.get_by_role("dialog", name="Navigation menu").is_visible()
                    page.keyboard.press("Escape")
                record = {
                    "width": width,
                    "route": route,
                    "status": response.status if response else None,
                    **metrics,
                    "console_errors": console_errors,
                }
                failed = failed or record["status"] != 200 or record["overflow"] or record["h1"] != 1 or bool(console_errors)
                results.append(record)
                page.close()
        browser.close()
    print(json.dumps(results, indent=2))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

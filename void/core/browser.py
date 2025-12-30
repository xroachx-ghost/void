"""
Browser automation wrapper built on Playwright.
"""

"""
Browser automation for Void.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

from datetime import datetime
import importlib.util
from pathlib import Path
from typing import Optional


class BrowserAutomation:
    """Simple wrapper around Playwright for GUI-driven automation."""

    def __init__(self, headless: bool = False, browser_name: str = "chromium") -> None:
        self.headless = headless
        self.browser_name = browser_name
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._sync_playwright = self._resolve_playwright()

    @property
    def is_active(self) -> bool:
        return self._page is not None

    def launch(self) -> None:
        if self.is_active:
            return
        self._playwright = self._sync_playwright().start()
        browser_type = getattr(self._playwright, self.browser_name, None)
        if browser_type is None:
            raise RuntimeError(f"Unsupported browser type: {self.browser_name}")
        self._browser = browser_type.launch(headless=self.headless)
        self._context = self._browser.new_context()
        self._page = self._context.new_page()

    def open(self, url: str) -> None:
        page = self._require_page()
        page.goto(url)

    def click(self, x: int, y: int) -> None:
        page = self._require_page()
        page.mouse.click(x, y)

    def type(self, text: str) -> None:
        page = self._require_page()
        page.keyboard.type(text)

    def screenshot(self, path: Optional[str] = None) -> str:
        page = self._require_page()
        if not path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"browser_screenshot_{timestamp}.png"
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(target), full_page=True)
        return str(target)

    def close(self) -> None:
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    def _require_page(self):
        if not self._page:
            raise RuntimeError("Browser not launched. Call launch() first.")
        return self._page

    def _resolve_playwright(self):
        if importlib.util.find_spec("playwright") is None:
            raise RuntimeError(
                "Playwright is not installed. Run 'pip install playwright' and "
                "'playwright install' to enable browser automation."
            )
        from playwright.sync_api import sync_playwright

        return sync_playwright

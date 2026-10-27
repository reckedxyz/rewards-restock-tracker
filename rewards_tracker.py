from __future__ import annotations

import os
import sys
import time

import requests
from playwright.sync_api import sync_playwright

DISCORD_WEBHOOK_URL = os.getenv("https://discord.com/api/webhooks/1561424246884798487/sR2oDDkG_QIL-EVxvDL-PH1mnbYTYNEdtuncKBbwytYGRf-2LT8RVVgnzjuWj4POG6QM")
DISCORD_USER_ID = os.getenv("899912455306747954")

# IMPORTANT: replace this with the actual rewards page URL
TARGET_URL = "https://rewards.bing.com/redeem/sku/000885000034"


def send_discord_message(message: str) -> None:
    if not DISCORD_WEBHOOK_URL:
        print("DISCORD_WEBHOOK_URL not set; skipping Discord notification.")
        return

    payload = {
        "content": f"<@{DISCORD_USER_ID}> {message}" if DISCORD_USER_ID else message,
    }

    response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=20)
    response.raise_for_status()
    print(f"Discord message sent: {message}")


def log(message: str) -> None:
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")


def wait_for_page_ready(page) -> None:
    page.wait_for_load_state("networkidle", timeout=20000)
    time.sleep(2)


def check_rewards() -> bool:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1200})

        try:
            log(f"Opening page: {TARGET_URL}")
            page.goto(TARGET_URL, timeout=60000, wait_until="domcontentloaded")
            wait_for_page_ready(page)

            body_text = page.locator("body").inner_text()
            lowered = body_text.lower()

            available_signals = [
                "available",
                "in stock",
                "restocked",
                "buy now",
                "claim",
            ]

            for signal in available_signals:
                if signal in lowered:
                    log(f"Detected availability signal: '{signal}'")
                    return True

            log("No restock indicators detected.")
            return False

        finally:
            browser.close()


def main() -> int:
    log("Starting rewards restock check")

    try:
        restocked = check_rewards()
        if restocked:
            send_discord_message("Rewards restock detected! Check the site now.")
            log("Restock detected and Discord notification sent.")
        else:
            log("No restock detected.")
        return 0
    except Exception as exc:
        log(f"Error during check: {exc}")
        send_discord_message(f"Rewards tracker failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

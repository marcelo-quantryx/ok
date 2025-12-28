#!/usr/bin/env python3
"""Prefect flow to scrape OK Mobility and notify on new cars via Telegram.

Environment vars required:
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID

Usage:
  source .venv/bin/activate
  python prefect_flow.py

To deploy with Prefect (example):
  prefect deployment build prefect_flow.py:main_flow -n "okmobility-every-5m" --apply
  prefect deployment run "okmobility-every-5m"  # or let the schedule run

Then configure schedule in Prefect UI or in deployment YAML (cron/interval every 5 minutes).
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any

from prefect import flow, get_run_logger

from scraper import OKMobilityScraper
import requests
from typing import Optional


DATA_DIR = Path(__file__).parent
LAST_SEEN_FILE = DATA_DIR / "last_seen.json"


def load_last_seen() -> List[str]:
    if not LAST_SEEN_FILE.exists():
        return []
    try:
        with LAST_SEEN_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_last_seen(ids: List[str]):
    with LAST_SEEN_FILE.open("w", encoding="utf-8") as f:
        json.dump(ids, f, indent=2, ensure_ascii=False)


def _load_secret_block(name: str) -> Optional[str]:
    """Try to load a Prefect Secret block, return None on failure."""
    try:
        from prefect.blocks.system import Secret
        try:
            blk = Secret.load(name)
            return blk.get()
        except Exception:
            return None
    except Exception:
        return None


def send_telegram_message(text: str):
    logger = get_run_logger()

    # Try Prefect Secret blocks first. Accept common block names (user example):
    # - "telegram-bot-token"
    # - "telegram-chat-id"
    # Also try legacy/uppercase env-style block names.
    token = _load_secret_block("telegram-bot-token") or _load_secret_block("TELEGRAM_BOT_TOKEN")
    chat_id = "77041861"

    # Fallback to environment variables if blocks are not available
    if not token:
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not chat_id:
        chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        logger.warning("Telegram credentials not set; skipping notification")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        logger.info("Telegram message sent")
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")


def extract_id(car: Dict[str, Any]) -> str:
    # Use booking_url if available, otherwise sipp_code
    return car.get("booking_url") or car.get("sipp_code") or json.dumps(car, sort_keys=True)


@flow(name="okmobility-scrape-and-notify")
def main_flow(
    url: str = "https://okmobility.com/en/subscription/booking/availability/sevilla-santa-justa-train-station/2026-01-05?onlyGuaranteedModels=false",
    persist_folder: str = ".",
):
    logger = get_run_logger()
    logger.info("Starting OK Mobility scrape")

    scraper = OKMobilityScraper()
    cars = scraper.scrape_from_url(url)
    logger.info(f"Scraped {len(cars)} cars")

    # Persist latest snapshot (overwrite single file)
    snapshot_file = DATA_DIR / "cars_latest.json"
    with snapshot_file.open("w", encoding="utf-8") as f:
        json.dump(cars, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved latest snapshot to {snapshot_file}")

    # Load last seen ids and compare
    last_seen = set(load_last_seen())
    current_ids = [extract_id(c) for c in cars]
    new_ids = [cid for cid in current_ids if cid not in last_seen]

    if new_ids:
        logger.info(f"Detected {len(new_ids)} new cars")
        # Find car records for new ids
        new_cars = [c for c in cars if extract_id(c) in new_ids]
        msg_lines = ["New cars available on OK Mobility:"]
        for c in new_cars:
            name = c.get("name") or c.get("sipp_code")
            price = c.get("pricing", {}).get("discounted_price")
            url_part = c.get("booking_url")
            if url_part and url_part.startswith("/"):
                full_url = f"https://okmobility.com{url_part}"
            else:
                full_url = url_part or url
            msg_lines.append(f"- {name} — €{price} — {full_url}")
        message = "\n".join(msg_lines)
        send_telegram_message(message)
    else:
        logger.info("No new cars detected")

    # Save current ids as last seen
    save_last_seen(current_ids)
    logger.info("Updated last seen list")


if __name__ == "__main__":
    main_flow()

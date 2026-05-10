"""Refresh A-share ticker aliases used by the web API.

The generated JSON maps Chinese stock short names and common code forms to
Yahoo-style tickers such as 600519.SH, 000001.SZ, and 920799.BJ.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_URL = "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData"
COUNT_URL = "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeStockCount"
PAGE_SIZE = 100
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "server" / "app" / "data" / "a_share_aliases.json"


def ticker_suffix(symbol: str, code: str) -> str | None:
    if symbol.startswith("sh"):
        return "SH"
    if symbol.startswith("sz"):
        return "SZ"
    if symbol.startswith("bj") or code.startswith(("8", "9")):
        return "BJ"
    return None


def fetch_json(url: str) -> object:
    request = Request(url, headers={"User-Agent": "TradingAgents/0.2"})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_total() -> int:
    query = urlencode(
        {
            "node": "hs_a",
        }
    )
    payload = fetch_json(f"{COUNT_URL}?{query}")
    return int(payload)


def fetch_page(page: int) -> list[dict]:
    query = urlencode(
        {
            "page": page,
            "num": PAGE_SIZE,
            "sort": "symbol",
            "asc": 1,
            "node": "hs_a",
            "symbol": "",
            "_s_r_a": "page",
        }
    )
    url = f"{API_URL}?{query}"
    for attempt in range(1, 4):
        try:
            payload = fetch_json(url)
            if not isinstance(payload, list):
                return []
            return payload
        except (HTTPError, URLError) as exc:
            time.sleep(attempt * 1.5)
            print(f"Retrying page {page} after {exc}", file=sys.stderr)
    curl = shutil.which("curl")
    if curl:
        result = subprocess.run(
            [curl, "-fsSL", "-A", "TradingAgents/0.2", url],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        payload = json.loads(result.stdout)
        if not isinstance(payload, list):
            return []
        return payload
    raise RuntimeError(f"Failed to fetch page {page}")


def build_aliases() -> tuple[dict[str, str], int]:
    aliases: dict[str, str] = {}
    page = 1
    total = fetch_total()
    listed_count = 0
    while True:
        rows = fetch_page(page)
        if not rows:
            break

        for row in rows:
            symbol = str(row.get("symbol") or "").strip().lower()
            code = str(row.get("code") or "").strip()
            name = str(row.get("name") or "").strip()
            suffix = ticker_suffix(symbol, code)
            if not code or not name or suffix is None:
                continue
            ticker = f"{code}.{suffix}"
            listed_count += 1
            aliases[name] = ticker
            aliases[code] = ticker
            aliases[f"{code}{suffix}"] = ticker
            aliases[ticker] = ticker
            aliases[f"{name}{code}"] = ticker
            aliases[f"{name}{ticker}"] = ticker

        if page * PAGE_SIZE >= total:
            break
        page += 1

    return dict(sorted(aliases.items(), key=lambda item: item[0])), listed_count


def main() -> int:
    aliases, listed_count = build_aliases()
    if listed_count < 5000:
        print(f"Refusing to write a suspiciously small A-share list: {listed_count}", file=sys.stderr)
        return 1

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "Sina Finance Market_Center hs_a API",
        "listed_count": listed_count,
        "aliases": aliases,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(aliases)} aliases for {listed_count} A-share listings to {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Ticker normalization helpers for the cloud API layer."""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path

from tradingagents.dataflows.utils import safe_ticker_component


DEFAULT_TICKER_ALIASES = {
    "300502": "300502.SZ",
    "300502SZ": "300502.SZ",
    "300502.SZ": "300502.SZ",
    "新易盛": "300502.SZ",
    "新易盛300502": "300502.SZ",
    "新易盛300502.SZ": "300502.SZ",
    "新易盛科技": "300502.SZ",
    "成都新易盛": "300502.SZ",
    "成都新易盛通信": "300502.SZ",
    "成都新易盛通信技术股份有限公司": "300502.SZ",
}

ALIAS_DATA_PATH = Path(__file__).with_name("data") / "a_share_aliases.json"


def _clean_alias_map(raw: object) -> dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    aliases: dict[str, str] = {}
    for key, value in raw.items():
        alias = str(key).strip()
        ticker = str(value).strip().upper()
        if not alias or not ticker:
            continue
        try:
            aliases[alias] = safe_ticker_component(ticker)
        except ValueError:
            continue
    return aliases


@lru_cache(maxsize=1)
def _load_a_share_aliases() -> dict[str, str]:
    if not ALIAS_DATA_PATH.exists():
        return {}
    try:
        payload = json.loads(ALIAS_DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if isinstance(payload, dict) and "aliases" in payload:
        payload = payload["aliases"]
    return _clean_alias_map(payload)


def _load_env_aliases() -> dict[str, str]:
    raw = os.getenv("TRADINGAGENTS_TICKER_ALIASES")
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return _clean_alias_map(parsed)


def ticker_aliases() -> dict[str, str]:
    aliases = _load_a_share_aliases()
    aliases.update(DEFAULT_TICKER_ALIASES)
    aliases.update(_load_env_aliases())
    return aliases


def _compact(value: str) -> str:
    return (
        value.strip()
        .replace(" ", "")
        .replace("\t", "")
        .replace("（", "(")
        .replace("）", ")")
        .replace("。", ".")
    )


def normalize_ticker(value: str) -> str:
    raw = value.strip()
    aliases = ticker_aliases()
    compact = _compact(raw)
    alias_keys = (raw, raw.upper(), compact, compact.upper())
    for key in alias_keys:
        if key in aliases:
            return safe_ticker_component(aliases[key].upper())

    for token in re.findall(r"[A-Za-z0-9\^][A-Za-z0-9._\-\^]{1,31}", compact):
        token_upper = token.upper()
        if token_upper in aliases:
            return safe_ticker_component(aliases[token_upper].upper())
        if token_upper.isdigit() and token_upper in aliases:
            return safe_ticker_component(aliases[token_upper].upper())
        try:
            return safe_ticker_component(token_upper)
        except ValueError:
            continue

    normalized = raw.upper()
    try:
        return safe_ticker_component(normalized)
    except ValueError as exc:
        raise ValueError(
            "Use an exchange ticker symbol, for example NVDA, SPY, "
            "300502.SZ, 0700.HK. Chinese names can be added through "
            "TRADINGAGENTS_TICKER_ALIASES."
        ) from exc

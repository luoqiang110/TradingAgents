import json

import pytest

from server.app.tickers import normalize_ticker, ticker_aliases


@pytest.mark.unit
def test_normalize_ticker_accepts_generated_a_share_names():
    assert normalize_ticker("贵州茅台") == "600519.SH"
    assert normalize_ticker("宁德时代") == "300750.SZ"
    assert normalize_ticker("安徽凤凰") == "920000.BJ"


@pytest.mark.unit
def test_normalize_ticker_accepts_a_share_code_forms():
    assert normalize_ticker("600519") == "600519.SH"
    assert normalize_ticker("300750SZ") == "300750.SZ"
    assert normalize_ticker("安徽凤凰920000.BJ") == "920000.BJ"


@pytest.mark.unit
def test_env_aliases_override_generated_aliases(monkeypatch):
    monkeypatch.setenv("TRADINGAGENTS_TICKER_ALIASES", json.dumps({"贵州茅台": "BABA"}))
    assert ticker_aliases()["贵州茅台"] == "BABA"
    assert normalize_ticker("贵州茅台") == "BABA"

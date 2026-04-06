"""
tests/test_insider.py
Basic tests for insider trading tools.
"""

import json
from tools.insider import _safe_df, get_market_insiders, get_insider_by_owner


def test_safe_df_empty():
    """Test _safe_df with None."""
    result = _safe_df(None)
    assert result == []


def test_get_market_insiders_returns_dict():
    """Test that get_market_insiders returns a valid dict with data."""
    result = get_market_insiders(option="latest buys", limit=5)
    assert result["status"] == "success"
    assert "data" in result
    assert "count" in result
    assert isinstance(result["data"], list)


def test_get_market_insiders_limit():
    """Test that limit parameter is respected."""
    result = get_market_insiders(option="latest buys", limit=3)
    assert len(result["data"]) <= 3
    assert result["count"] <= 3


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])

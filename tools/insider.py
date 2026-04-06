"""
tools/insider.py
Market-wide insider trading tools (not ticker-specific).
"""

import json

from finvizfinance.insider import Insider


def _safe_df(df):
    if df is None:
        return []
    df = df.fillna("").infer_objects(copy=False)
    return json.loads(df.to_json(orient="records"))


def register_insider_tools(mcp):

    @mcp.tool()
    def finviz_get_market_insiders(
        option: str = "latest buys",
        limit: int = 30,
    ) -> str:
        """
        Returns market-wide insider trading activity from Finviz.

        Args:
            option: Type of insider activity to retrieve. Options:
                "latest"           – Most recent insider transactions (buys + sells).
                "latest buys"      – Most recent insider purchases only.
                "latest sales"     – Most recent insider sales only.
                "top week"         – Largest insider transactions this week.
                "top week buys"    – Largest insider purchases this week.
                "top week sales"   – Largest insider sales this week.
                "top owner trade"  – Largest trades by major owners (>$1M).
                "top owner buys"   – Largest purchases by major owners.
                "top owner sales"  – Largest sales by major owners.
                Default: "latest buys".
            limit: Maximum number of rows to return. Default 30.

        Returns:
            JSON array with fields: Ticker, Owner, Relationship, Date,
            Transaction, #Shares, Cost, Value ($), #Shares Total, SEC Form 4 Link.

        Use-case: Spot stocks with significant insider buying for bullish confirmation.
        """
        ins = Insider(option=option)
        df = ins.get_insider()
        records = _safe_df(df)
        return json.dumps(records[:limit], indent=2)

    @mcp.tool()
    def finviz_get_insider_by_owner(
        insider_id: str,
        limit: int = 30,
    ) -> str:
        """
        Returns all transactions for a specific insider (by their Finviz insider ID).

        Args:
            insider_id: Numeric Finviz insider ID (found in the "Insider_id" field
                        returned by finviz_get_ticker_insider or finviz_get_market_insiders).
            limit: Maximum number of rows. Default 30.

        Returns:
            JSON array of that insider's transactions.
        """
        ins = Insider(option=str(insider_id))
        df = ins.get_insider()
        records = _safe_df(df)
        return json.dumps(records[:limit], indent=2)

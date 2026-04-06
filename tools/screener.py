"""
tools/screener.py
Stock screener tools wrapping finvizfinance screener module.
"""

import json

from finvizfinance.screener.overview import Overview
from finvizfinance.screener.technical import Technical
from finvizfinance.screener.performance import Performance


def _df_to_records(df):
    if df is None:
        return []
    df = df.fillna("")
    return json.loads(df.to_json(orient="records"))


def register_screener_tools(mcp):

    @mcp.tool()
    def finviz_screen_new_highs(
        sector: str = "",
        min_market_cap: str = "+Mid (over $2bln)",
        min_avg_volume: str = "Over 500K",
        limit: int = 50,
    ) -> str:
        """
        Screens for stocks hitting 52-week new highs (strong breakout signal).

        Args:
            sector: Filter by sector, e.g. "Technology", "Healthcare", "Financial".
                    Leave empty for all sectors.
            min_market_cap: Minimum market cap filter. Options:
                "Mega ($200bln and more)", "Large ($10bln to $200bln)",
                "+Large (over $10bln)", "+Mid (over $2bln)", "+Small (over $300mln)".
                Default: "+Mid (over $2bln)".
            min_avg_volume: Minimum average volume. Options:
                "Over 100K", "Over 200K", "Over 500K", "Over 1M", "Over 2M".
                Default: "Over 500K".
            limit: Max number of results. Default 50.

        Returns:
            JSON array of ticker rows (Ticker, Company, Sector, Industry,
            Market Cap, Price, Change, Volume, etc.).

        Use-case: Find stocks breaking out to new highs — momentum candidates.
        """
        s = Overview()
        filters = {"Average Volume": min_avg_volume, "Market Cap.": min_market_cap}
        if sector:
            filters["Sector"] = sector
        s.set_filter(signal="New High", filters_dict=filters)
        df = s.screener_view(order="Performance (Week)", ascend=False,
                             limit=limit, verbose=0)
        return json.dumps(_df_to_records(df), indent=2)

    @mcp.tool()
    def finviz_screen_bullish_technicals(
        sector: str = "",
        min_market_cap: str = "+Mid (over $2bln)",
        min_avg_volume: str = "Over 500K",
        sma50_filter: str = "Price above SMA50",
        sma200_filter: str = "Price above SMA200",
        rsi_filter: str = "Not Oversold (>50)",
        performance_filter: str = "Quarter Up",
        limit: int = 50,
    ) -> str:
        """
        Screens for stocks with bullish technical setup (above SMAs, momentum).

        Args:
            sector: Sector filter, e.g. "Technology". Empty = all sectors.
            min_market_cap: Market cap filter. Default "+Mid (over $2bln)".
            min_avg_volume: Volume filter. Default "Over 500K".
            sma50_filter: SMA50 condition. Common options:
                "Price above SMA50", "Price 10% above SMA50",
                "Price crossed SMA50 above". Default "Price above SMA50".
            sma200_filter: SMA200 condition. Common options:
                "Price above SMA200", "Price crossed SMA200 above".
                Default "Price above SMA200".
            rsi_filter: RSI filter. Options:
                "Not Oversold (>50)", "Not Oversold (>40)",
                "Overbought (60)", "Overbought (70)".
                Default "Not Oversold (>50)".
            performance_filter: Performance filter. Options:
                "Quarter Up", "Quarter +10%", "Quarter +20%",
                "Month Up", "Month +10%", "Year Up".
                Default "Quarter Up".
            limit: Max results. Default 50.

        Returns:
            JSON array of tickers with overview data.
        """
        s = Overview()
        filters = {
            "Market Cap.": min_market_cap,
            "Average Volume": min_avg_volume,
            "50-Day Simple Moving Average": sma50_filter,
            "200-Day Simple Moving Average": sma200_filter,
            "RSI (14)": rsi_filter,
            "Performance": performance_filter,
        }
        if sector:
            filters["Sector"] = sector
        s.set_filter(filters_dict=filters)
        df = s.screener_view(order="Performance (Quarter)", ascend=False,
                             limit=limit, verbose=0)
        return json.dumps(_df_to_records(df), indent=2)

    @mcp.tool()
    def finviz_screen_by_signal(
        signal: str,
        sector: str = "",
        min_market_cap: str = "+Small (over $300mln)",
        min_avg_volume: str = "Over 200K",
        limit: int = 50,
    ) -> str:
        """
        Screens stocks by a Finviz technical/news signal.

        Args:
            signal: The signal to screen. Available signals:
                Technical patterns: "New High", "New Low", "Top Gainers", "Top Losers",
                "Most Volatile", "Most Active", "Unusual Volume", "Overbought",
                "Oversold", "Channel Up", "Channel Down", "TL Support",
                "TL Resistance", "Wedge Up", "Wedge Down",
                "Triangle Ascending", "Triangle Descending",
                "Double Bottom", "Double Top", "Head & Shoulders",
                "Head & Shoulders Inverse".
                News/insider: "Upgrades", "Downgrades",
                "Recent Insider Buying", "Recent Insider Selling",
                "Earnings Before", "Earnings After", "Major News".
            sector: Optional sector filter.
            min_market_cap: Market cap filter. Default "+Small (over $300mln)".
            min_avg_volume: Volume filter. Default "Over 200K".
            limit: Max results. Default 50.

        Returns:
            JSON array of ticker rows.
        """
        s = Overview()
        filters = {
            "Market Cap.": min_market_cap,
            "Average Volume": min_avg_volume,
        }
        if sector:
            filters["Sector"] = sector
        s.set_filter(signal=signal, filters_dict=filters)
        df = s.screener_view(limit=limit, verbose=0)
        return json.dumps(_df_to_records(df), indent=2)

    @mcp.tool()
    def finviz_screen_technical(
        sector: str = "",
        min_market_cap: str = "+Mid (over $2bln)",
        min_avg_volume: str = "Over 500K",
        limit: int = 50,
    ) -> str:
        """
        Returns technical screener data (RSI, Beta, ATR, SMA distances, volatility)
        for stocks matching basic filters.

        Args:
            sector: Sector filter. Empty = all.
            min_market_cap: Market cap filter. Default "+Mid (over $2bln)".
            min_avg_volume: Volume filter. Default "Over 500K".
            limit: Max results. Default 50.

        Returns:
            JSON array with RSI, Beta, ATR, SMA20/50/200 distance, volatility columns.
        """
        s = Technical()
        filters = {
            "Market Cap.": min_market_cap,
            "Average Volume": min_avg_volume,
            "50-Day Simple Moving Average": "Price above SMA50",
            "200-Day Simple Moving Average": "Price above SMA200",
        }
        if sector:
            filters["Sector"] = sector
        s.set_filter(filters_dict=filters)
        df = s.screener_view(order="Relative Strength Index (14)", ascend=False,
                             limit=limit, verbose=0)
        return json.dumps(_df_to_records(df), indent=2)

    @mcp.tool()
    def finviz_screen_performance(
        sector: str = "",
        min_market_cap: str = "+Mid (over $2bln)",
        min_avg_volume: str = "Over 500K",
        sort_by: str = "Performance (Quarter)",
        limit: int = 50,
    ) -> str:
        """
        Returns performance screener data (weekly/monthly/quarterly/yearly returns)
        for stocks matching filters. Good for momentum ranking.

        Args:
            sector: Sector filter. Empty = all.
            min_market_cap: Market cap filter. Default "+Mid (over $2bln)".
            min_avg_volume: Volume filter. Default "Over 500K".
            sort_by: Sort column. Options: "Performance (Week)",
                "Performance (Month)", "Performance (Quarter)",
                "Performance (Half Year)", "Performance (Year)",
                "Performance (Year To Date)".
                Default "Performance (Quarter)".
            limit: Max results. Default 50.

        Returns:
            JSON array with performance columns.
        """
        s = Performance()
        filters = {
            "Market Cap.": min_market_cap,
            "Average Volume": min_avg_volume,
            "50-Day Simple Moving Average": "Price above SMA50",
            "200-Day Simple Moving Average": "Price above SMA200",
        }
        if sector:
            filters["Sector"] = sector
        s.set_filter(filters_dict=filters)
        df = s.screener_view(order=sort_by, ascend=False, limit=limit, verbose=0)
        return json.dumps(_df_to_records(df), indent=2)

    @mcp.tool()
    def finviz_screen_optionable_bullish(
        sector: str = "",
        min_market_cap: str = "+Mid (over $2bln)",
        min_avg_volume: str = "Over 500K",
        limit: int = 50,
    ) -> str:
        """
        Screens for optionable stocks with bullish technical setup.
        Filters: optionable + shortable, above SMA50 & SMA200, RSI > 50,
        quarterly performance positive.

        Args:
            sector: Optional sector filter.
            min_market_cap: Market cap filter. Default "+Mid (over $2bln)".
            min_avg_volume: Volume filter. Default "Over 500K".
            limit: Max results. Default 50.

        Returns:
            JSON array — ideal candidates for options strategies (PMCC, spreads, etc.).
        """
        s = Overview()
        filters = {
            "Market Cap.": min_market_cap,
            "Average Volume": min_avg_volume,
            "Option/Short": "Optionable and shortable",
            "50-Day Simple Moving Average": "Price above SMA50",
            "200-Day Simple Moving Average": "Price above SMA200",
            "RSI (14)": "Not Oversold (>50)",
            "Performance": "Quarter Up",
        }
        if sector:
            filters["Sector"] = sector
        s.set_filter(filters_dict=filters)
        df = s.screener_view(order="Performance (Quarter)", ascend=False,
                             limit=limit, verbose=0)
        return json.dumps(_df_to_records(df), indent=2)

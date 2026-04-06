"""
tools/group.py
Sector / Industry / Group analysis from Finviz.
"""

import json

from finvizfinance.group.performance import Performance as GroupPerformance
from finvizfinance.group.overview import Overview as GroupOverview


def _df_to_records(df):
    if df is None:
        return []
    df = df.fillna("")
    return json.loads(df.to_json(orient="records"))


def register_group_tools(mcp):

    @mcp.tool()
    def finviz_get_sector_performance(
        period: str = "Performance (Quarter)",
        top_n: int = 11,
    ) -> str:
        """
        Returns sector performance table from Finviz, sorted by the chosen period.

        Args:
            period: Sorting period. One of:
                "Performance (Week)", "Performance (Month)",
                "Performance (Quarter)", "Performance (Half Year)",
                "Performance (Year)", "Performance (Year To Date)",
                "Change" (today).
                Default: "Performance (Quarter)".
            top_n: Number of sectors to return (max 11). Default 11 (all).

        Returns:
            JSON array of sector rows with Name, Change, and performance columns.

        Use-case: Identify the leading US sectors before running a stock screener.
        """
        g = GroupPerformance()
        df = g.screener_view(group="Sector", order=period)
        if df is None:
            return json.dumps([])
        # Sort descending by the period column if it exists
        if period in df.columns:
            df = df.sort_values(period, ascending=False)
        records = _df_to_records(df.head(top_n))
        return json.dumps(records, indent=2)

    @mcp.tool()
    def finviz_get_industry_performance(
        sector: str = "",
        period: str = "Performance (Quarter)",
        top_n: int = 20,
    ) -> str:
        """
        Returns industry performance within a specific sector (or all industries).

        Args:
            sector: Filter to a specific sector's industries, e.g.
                "Technology", "Healthcare", "Financial", "Energy",
                "Industrials", "Consumer Cyclical", "Consumer Defensive",
                "Communication Services", "Basic Materials",
                "Real Estate", "Utilities".
                Leave empty for all industries.
            period: Sort period (same options as finviz_get_sector_performance).
            top_n: Number of industries to return. Default 20.

        Returns:
            JSON array of industry rows sorted by performance.
        """
        g = GroupPerformance()
        group_key = f"Industry ({sector})" if sector else "Industry"
        df = g.screener_view(group=group_key, order=period)
        if df is None:
            return json.dumps([])
        if period in df.columns:
            df = df.sort_values(period, ascending=False)
        records = _df_to_records(df.head(top_n))
        return json.dumps(records, indent=2)

    @mcp.tool()
    def finviz_get_group_overview(
        group: str = "Sector",
    ) -> str:
        """
        Returns a fundamental overview (Market Cap, P/E, EPS growth, etc.) for a group.

        Args:
            group: One of "Sector", "Industry", "Country", "Capitalization",
                or industry sub-groups like "Industry (Technology)".
                Default: "Sector".

        Returns:
            JSON array of group rows with market cap, valuation, and growth metrics.
        """
        g = GroupOverview()
        df = g.screener_view(group=group, order="Market Capitalization")
        if df is None:
            return json.dumps([])
        return json.dumps(_df_to_records(df), indent=2)

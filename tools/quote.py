"""
tools/quote.py
Individual ticker detail tools (fundamentals, news, insider, ratings, peers).
"""

import json

from finvizfinance.quote import finvizfinance


def _safe_df(df):
    if df is None:
        return []
    df = df.fillna("").infer_objects(copy=False)
    # Convert datetime columns to string for JSON serialisation
    for col in df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
        df[col] = df[col].astype(str)
    return json.loads(df.to_json(orient="records"))


def register_quote_tools(mcp):

    @mcp.tool()
    def finviz_get_ticker_fundamentals(ticker: str) -> str:
        """
        Returns key fundamentals for a single ticker from Finviz quote page.

        Includes: Company, Sector, Industry, Country, Exchange, Market Cap,
        P/E, Forward P/E, PEG, EPS, EPS next Y, Revenue, ROE, ROA,
        Debt/Eq, Insider Own, Inst Own, Short Float, Analyst Recom,
        52W High/Low, RSI, Beta, ATR, SMA distances, Volume, etc.

        Args:
            ticker: Stock ticker symbol, e.g. "AAPL", "NVDA", "MSFT".

        Returns:
            JSON object (dict) with all available fundamental fields.
        """
        stock = finvizfinance(ticker.upper())
        data = stock.ticker_fundament()
        # Ensure all values are JSON-serialisable
        clean = {k: str(v) if not isinstance(v, (int, float, str, type(None))) else v
                 for k, v in data.items()}
        return json.dumps(clean, indent=2)

    @mcp.tool()
    def finviz_get_ticker_news(ticker: str, max_items: int = 20) -> str:
        """
        Returns the latest news for a ticker from the Finviz quote page.

        Args:
            ticker: Stock ticker symbol.
            max_items: Maximum number of news items to return. Default 20.

        Returns:
            JSON array of news items with fields: Date, Title, Link, Source.

        Use-case: Quick news sentiment check before entering a trade.
        """
        stock = finvizfinance(ticker.upper())
        df = stock.ticker_news()
        records = _safe_df(df)
        return json.dumps(records[:max_items], indent=2)

    @mcp.tool()
    def finviz_get_ticker_insider(ticker: str) -> str:
        """
        Returns recent insider trading activity for a ticker.

        Args:
            ticker: Stock ticker symbol.

        Returns:
            JSON array of insider transactions with fields:
            Trader, Relationship, Date, Transaction, #Shares, Cost,
            Value ($), #Shares Total, SEC Form 4 Link.

        Use-case: Detect insider buying as a bullish confirmation signal.
        """
        stock = finvizfinance(ticker.upper())
        df = stock.ticker_inside_trader()
        return json.dumps(_safe_df(df), indent=2)

    @mcp.tool()
    def finviz_get_ticker_ratings(ticker: str) -> str:
        """
        Returns analyst ratings history for a ticker.

        Args:
            ticker: Stock ticker symbol.

        Returns:
            JSON array with fields: Date, Status (Upgrade/Downgrade/Initiated/etc.),
            Outer (analyst firm), Rating, Price (target).
        """
        stock = finvizfinance(ticker.upper())
        df = stock.ticker_outer_ratings()
        return json.dumps(_safe_df(df), indent=2)

    @mcp.tool()
    def finviz_get_ticker_peers(ticker: str) -> str:
        """
        Returns peer tickers for a given stock (same sector/industry).

        Args:
            ticker: Stock ticker symbol.

        Returns:
            JSON array of peer ticker symbols (strings).

        Use-case: Quickly find comparable stocks for a sector play.
        """
        stock = finvizfinance(ticker.upper())
        peers = stock.ticker_peer()
        return json.dumps(peers, indent=2)

    @mcp.tool()
    def finviz_get_ticker_full_info(ticker: str) -> str:
        """
        Returns all available information for a ticker in one call:
        fundamentals, news (latest 10), insider trades, analyst ratings.

        Args:
            ticker: Stock ticker symbol.

        Returns:
            JSON object with keys: "fundament", "news", "inside_trader", "ratings".

        Use-case: Deep-dive on a candidate before proposing a trade idea.
        """
        stock = finvizfinance(ticker.upper())
        fundament = stock.ticker_fundament()
        clean_fund = {k: str(v) if not isinstance(v, (int, float, str, type(None))) else v
                      for k, v in fundament.items()}

        news_df = stock.ticker_news()
        insider_df = stock.ticker_inside_trader()
        ratings_df = stock.ticker_outer_ratings()

        result = {
            "fundament": clean_fund,
            "news": _safe_df(news_df)[:10],
            "inside_trader": _safe_df(insider_df),
            "ratings": _safe_df(ratings_df),
            "peers": stock.ticker_peer(),
        }
        return json.dumps(result, indent=2)

    @mcp.tool()
    def finviz_get_ticker_description(ticker: str) -> str:
        """
        Returns the company business description for a ticker.

        Args:
            ticker: Stock ticker symbol.

        Returns:
            Plain text company description.
        """
        stock = finvizfinance(ticker.upper())
        return stock.ticker_description()

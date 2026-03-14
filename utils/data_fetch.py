"""Real market data fetching via yfinance."""

import yfinance as yf


def get_prices(
    ticker: str, period: str = "2y", interval: str = "1mo"
) -> list[float]:
    """Fetch historical closing prices for a ticker.

    Args:
        ticker: Yahoo Finance ticker symbol (e.g. 'AAPL', '^GSPC').
        period: Lookback period ('1y', '2y', '5y', '10y', 'max').
        interval: Data interval ('1d', '1wk', '1mo').

    Returns:
        List of closing prices.
    """
    data = yf.download(ticker, period=period, interval=interval, progress=False)
    if data.empty:
        raise ValueError(f"No data found for {ticker}")
    closes = data["Close"].dropna().tolist()
    # yfinance may return nested lists for single tickers
    if closes and isinstance(closes[0], list):
        closes = [c[0] for c in closes]
    return closes


def get_multi_prices(
    tickers: list[str], period: str = "2y", interval: str = "1mo"
) -> dict[str, list[float]]:
    """Fetch historical closing prices for multiple tickers.

    Args:
        tickers: List of Yahoo Finance ticker symbols.
        period: Lookback period.
        interval: Data interval.

    Returns:
        Dict mapping ticker to list of closing prices.
    """
    result = {}
    for ticker in tickers:
        try:
            result[ticker] = get_prices(ticker, period, interval)
        except (ValueError, Exception):
            continue
    return result


def get_info(ticker: str) -> dict:
    """Fetch key financial info for a ticker.

    Args:
        ticker: Yahoo Finance ticker symbol.

    Returns:
        Dict with keys like 'marketCap', 'trailingPE', 'forwardPE',
        'dividendYield', 'beta', 'fiftyTwoWeekHigh', 'fiftyTwoWeekLow', etc.
    """
    t = yf.Ticker(ticker)
    return dict(t.info)


def get_financials(ticker: str) -> dict:
    """Fetch income statement, balance sheet, and cash flow data.

    Args:
        ticker: Yahoo Finance ticker symbol.

    Returns:
        Dict with 'income_statement', 'balance_sheet', 'cashflow' as
        DataFrames converted to dicts.
    """
    t = yf.Ticker(ticker)
    return {
        "income_statement": t.income_stmt.to_dict() if t.income_stmt is not None else {},
        "balance_sheet": t.balance_sheet.to_dict() if t.balance_sheet is not None else {},
        "cashflow": t.cashflow.to_dict() if t.cashflow is not None else {},
    }

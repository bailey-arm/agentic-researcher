"""Risk and return analytics utilities."""

import math


def returns(prices: list[float]) -> list[float]:
    """Calculate period-over-period percentage returns from a price series.

    Args:
        prices: List of prices (at least 2).

    Returns:
        List of percentage returns (length = len(prices) - 1).
    """
    if len(prices) < 2:
        raise ValueError("Need at least 2 prices")
    return [(prices[i] / prices[i - 1] - 1) * 100 for i in range(1, len(prices))]


def volatility(prices: list[float], annualize: int = 12) -> float:
    """Calculate annualized volatility from a price series.

    Args:
        prices: List of prices (e.g. monthly closes).
        annualize: Periods per year (12 for monthly, 252 for daily).

    Returns:
        Annualized volatility as a percentage.
    """
    rets = returns(prices)
    n = len(rets)
    mean = sum(rets) / n
    variance = sum((r - mean) ** 2 for r in rets) / (n - 1)
    return math.sqrt(variance) * math.sqrt(annualize)


def sharpe_ratio(
    prices: list[float], risk_free_rate: float = 2.0, annualize: int = 12
) -> float:
    """Calculate annualized Sharpe ratio.

    Args:
        prices: List of prices.
        risk_free_rate: Annual risk-free rate as a percentage.
        annualize: Periods per year.

    Returns:
        Sharpe ratio.
    """
    rets = returns(prices)
    mean_return = sum(rets) / len(rets)
    annualized_return = mean_return * annualize
    vol = volatility(prices, annualize)
    if vol == 0:
        return 0.0
    return (annualized_return - risk_free_rate) / vol


def max_drawdown(prices: list[float]) -> float:
    """Calculate maximum drawdown from a price series.

    Args:
        prices: List of prices.

    Returns:
        Maximum drawdown as a negative percentage.
    """
    if len(prices) < 2:
        raise ValueError("Need at least 2 prices")
    peak = prices[0]
    max_dd = 0.0
    for price in prices:
        if price > peak:
            peak = price
        dd = (price / peak - 1) * 100
        if dd < max_dd:
            max_dd = dd
    return max_dd


def value_at_risk(prices: list[float], confidence: float = 0.95) -> float:
    """Calculate historical Value at Risk.

    Args:
        prices: List of prices.
        confidence: Confidence level (e.g. 0.95 for 95%).

    Returns:
        VaR as a percentage (negative number representing potential loss).
    """
    rets = sorted(returns(prices))
    index = int((1 - confidence) * len(rets))
    return rets[max(index, 0)]


def sortino_ratio(
    prices: list[float], risk_free_rate: float = 2.0, annualize: int = 12
) -> float:
    """Calculate annualized Sortino ratio (penalizes only downside volatility).

    Args:
        prices: List of prices.
        risk_free_rate: Annual risk-free rate as a percentage.
        annualize: Periods per year.

    Returns:
        Sortino ratio.
    """
    rets = returns(prices)
    mean_return = sum(rets) / len(rets)
    annualized_return = mean_return * annualize
    downside = [r for r in rets if r < 0]
    if not downside:
        return float("inf")
    downside_var = sum(r**2 for r in downside) / len(downside)
    downside_vol = math.sqrt(downside_var) * math.sqrt(annualize)
    if downside_vol == 0:
        return 0.0
    return (annualized_return - risk_free_rate) / downside_vol


def risk_summary(assets: dict[str, list[float]], annualize: int = 12) -> list[dict]:
    """Generate a risk summary table for multiple assets.

    Args:
        assets: Dict mapping asset name to price history.
        annualize: Periods per year.

    Returns:
        List of dicts with name, volatility, sharpe, max_drawdown, var_95.
    """
    results = []
    for name, prices in assets.items():
        try:
            results.append({
                "name": name,
                "volatility": round(volatility(prices, annualize), 2),
                "sharpe": round(sharpe_ratio(prices, annualize=annualize), 2),
                "max_drawdown": round(max_drawdown(prices), 2),
                "var_95": round(value_at_risk(prices), 2),
            })
        except (ValueError, ZeroDivisionError):
            continue
    return results

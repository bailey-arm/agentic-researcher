"""Simple momentum calculation utilities."""


def calculate_momentum(prices: list[float], period: int = 12) -> float:
    """Calculate price momentum as percentage change over a period.

    Args:
        prices: List of prices (e.g. monthly closing prices).
        period: Lookback period (default 12 for 12-month momentum).

    Returns:
        Momentum as a percentage change.
    """
    if len(prices) <= period:
        raise ValueError(f"Need more than {period} prices, got {len(prices)}")
    return (prices[-1] / prices[-period] - 1) * 100


def rank_by_momentum(assets: dict[str, list[float]], period: int = 12) -> list[tuple[str, float]]:
    """Rank assets by momentum, highest first.

    Args:
        assets: Dict mapping asset name to price history.
        period: Lookback period.

    Returns:
        List of (asset_name, momentum) tuples sorted descending.
    """
    results = []
    for name, prices in assets.items():
        try:
            mom = calculate_momentum(prices, period)
            results.append((name, mom))
        except ValueError:
            continue
    return sorted(results, key=lambda x: x[1], reverse=True)

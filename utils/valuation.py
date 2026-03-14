"""Valuation metric utilities."""


def pe_ratio(price: float, earnings_per_share: float) -> float:
    """Calculate Price-to-Earnings ratio.

    Args:
        price: Current share price.
        earnings_per_share: Trailing twelve month EPS.

    Returns:
        P/E ratio.
    """
    if earnings_per_share == 0:
        raise ValueError("EPS cannot be zero")
    return price / earnings_per_share


def earnings_yield(price: float, earnings_per_share: float) -> float:
    """Calculate earnings yield (inverse of P/E) as a percentage.

    Args:
        price: Current share price.
        earnings_per_share: Trailing twelve month EPS.

    Returns:
        Earnings yield as a percentage.
    """
    if price == 0:
        raise ValueError("Price cannot be zero")
    return (earnings_per_share / price) * 100


def peg_ratio(pe: float, earnings_growth_rate: float) -> float:
    """Calculate PEG ratio (P/E divided by earnings growth rate).

    Args:
        pe: Price-to-Earnings ratio.
        earnings_growth_rate: Expected annual earnings growth as a percentage.

    Returns:
        PEG ratio. Values below 1 may indicate undervaluation.
    """
    if earnings_growth_rate == 0:
        raise ValueError("Earnings growth rate cannot be zero")
    return pe / earnings_growth_rate


def price_to_book(price: float, book_value_per_share: float) -> float:
    """Calculate Price-to-Book ratio.

    Args:
        price: Current share price.
        book_value_per_share: Book value per share.

    Returns:
        P/B ratio.
    """
    if book_value_per_share == 0:
        raise ValueError("Book value per share cannot be zero")
    return price / book_value_per_share


def dividend_yield(annual_dividend: float, price: float) -> float:
    """Calculate dividend yield as a percentage.

    Args:
        annual_dividend: Annual dividend per share.
        price: Current share price.

    Returns:
        Dividend yield as a percentage.
    """
    if price == 0:
        raise ValueError("Price cannot be zero")
    return (annual_dividend / price) * 100


def rank_by_valuation(
    assets: dict[str, dict], metric: str = "pe"
) -> list[tuple[str, float]]:
    """Rank assets by a valuation metric, cheapest first.

    Args:
        assets: Dict mapping asset name to dict with keys
                'price', 'eps', 'growth_rate', 'book_value', 'dividend'.
        metric: One of 'pe', 'earnings_yield', 'peg', 'pb', 'dividend_yield'.

    Returns:
        List of (asset_name, metric_value) tuples sorted ascending
        (cheapest first for pe/peg/pb, highest first for yields).
    """
    results = []
    for name, data in assets.items():
        try:
            if metric == "pe":
                val = pe_ratio(data["price"], data["eps"])
            elif metric == "earnings_yield":
                val = earnings_yield(data["price"], data["eps"])
            elif metric == "peg":
                val = peg_ratio(
                    pe_ratio(data["price"], data["eps"]), data["growth_rate"]
                )
            elif metric == "pb":
                val = price_to_book(data["price"], data["book_value"])
            elif metric == "dividend_yield":
                val = dividend_yield(data["dividend"], data["price"])
            else:
                raise ValueError(f"Unknown metric: {metric}")
            results.append((name, val))
        except (ValueError, KeyError, ZeroDivisionError):
            continue

    reverse = metric in ("earnings_yield", "dividend_yield")
    return sorted(results, key=lambda x: x[1], reverse=reverse)

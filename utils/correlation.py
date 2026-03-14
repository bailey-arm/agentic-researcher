"""Cross-asset correlation utilities."""

import math


def _returns(prices: list[float]) -> list[float]:
    return [(prices[i] / prices[i - 1] - 1) for i in range(1, len(prices))]


def pearson_correlation(prices_a: list[float], prices_b: list[float]) -> float:
    """Calculate Pearson correlation between two price series' returns.

    Args:
        prices_a: First price series.
        prices_b: Second price series (same length as prices_a).

    Returns:
        Correlation coefficient between -1 and 1.
    """
    if len(prices_a) != len(prices_b):
        raise ValueError("Price series must be the same length")
    if len(prices_a) < 3:
        raise ValueError("Need at least 3 prices")

    ra = _returns(prices_a)
    rb = _returns(prices_b)
    n = len(ra)

    mean_a = sum(ra) / n
    mean_b = sum(rb) / n

    cov = sum((ra[i] - mean_a) * (rb[i] - mean_b) for i in range(n)) / (n - 1)
    std_a = math.sqrt(sum((r - mean_a) ** 2 for r in ra) / (n - 1))
    std_b = math.sqrt(sum((r - mean_b) ** 2 for r in rb) / (n - 1))

    if std_a == 0 or std_b == 0:
        return 0.0
    return cov / (std_a * std_b)


def correlation_matrix(
    assets: dict[str, list[float]],
) -> dict[str, dict[str, float]]:
    """Calculate pairwise correlation matrix for multiple assets.

    Args:
        assets: Dict mapping asset name to price history.
                All series must be the same length.

    Returns:
        Nested dict: matrix[asset_a][asset_b] = correlation.
    """
    names = list(assets.keys())
    matrix = {}
    for a in names:
        matrix[a] = {}
        for b in names:
            if a == b:
                matrix[a][b] = 1.0
            elif b in matrix and a in matrix[b]:
                matrix[a][b] = matrix[b][a]
            else:
                matrix[a][b] = round(
                    pearson_correlation(assets[a], assets[b]), 4
                )
    return matrix


def rolling_correlation(
    prices_a: list[float], prices_b: list[float], window: int = 12
) -> list[float | None]:
    """Calculate rolling correlation between two price series.

    Args:
        prices_a: First price series.
        prices_b: Second price series (same length).
        window: Rolling window size.

    Returns:
        List of correlations (None for initial periods without enough data).
    """
    if len(prices_a) != len(prices_b):
        raise ValueError("Price series must be the same length")

    results: list[float | None] = []
    for i in range(len(prices_a)):
        if i < window:
            results.append(None)
        else:
            segment_a = prices_a[i - window : i + 1]
            segment_b = prices_b[i - window : i + 1]
            results.append(round(pearson_correlation(segment_a, segment_b), 4))
    return results


def print_correlation_matrix(matrix: dict[str, dict[str, float]]) -> None:
    """Pretty-print a correlation matrix."""
    names = list(matrix.keys())
    # Header
    header = f"{'':>20}" + "".join(f"{n:>12}" for n in names)
    print(header)
    for a in names:
        row = f"{a:>20}" + "".join(f"{matrix[a][b]:>12.3f}" for b in names)
        print(row)

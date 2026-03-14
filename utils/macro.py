"""Macroeconomic analysis utilities."""


def yield_curve_slope(short_rate: float, long_rate: float) -> float:
    """Calculate yield curve slope (long minus short).

    Args:
        short_rate: Short-term yield (e.g. 2-year) as percentage.
        long_rate: Long-term yield (e.g. 10-year) as percentage.

    Returns:
        Spread in percentage points. Negative = inverted curve.
    """
    return long_rate - short_rate


def real_rate(nominal_rate: float, inflation_rate: float) -> float:
    """Calculate real interest rate (Fisher equation approximation).

    Args:
        nominal_rate: Nominal interest rate as percentage.
        inflation_rate: Inflation rate as percentage.

    Returns:
        Real rate as percentage.
    """
    return nominal_rate - inflation_rate


def pmi_trend(readings: list[float], window: int = 3) -> dict:
    """Analyze PMI trend and regime.

    Args:
        readings: List of PMI readings (most recent last).
        window: Number of recent readings for trend calculation.

    Returns:
        Dict with 'latest', 'average', 'trend' (expanding/contracting),
        'regime' (expansion/contraction), and 'momentum' (improving/deteriorating).
    """
    if len(readings) < window:
        raise ValueError(f"Need at least {window} readings")

    latest = readings[-1]
    recent = readings[-window:]
    avg = sum(recent) / len(recent)

    regime = "expansion" if latest >= 50 else "contraction"
    trend_dir = "expanding" if recent[-1] > recent[0] else "contracting"

    # Momentum: is the rate of change improving?
    if len(readings) >= window * 2:
        prev_avg = sum(readings[-window * 2 : -window]) / window
        momentum = "improving" if avg > prev_avg else "deteriorating"
    else:
        momentum = "insufficient data"

    return {
        "latest": latest,
        "average": round(avg, 1),
        "trend": trend_dir,
        "regime": regime,
        "momentum": momentum,
    }


def macro_regime(
    yield_slope: float, pmi: float, inflation: float, gdp_growth: float
) -> str:
    """Classify the current macro regime.

    Args:
        yield_slope: Yield curve slope (10y - 2y) in percentage points.
        pmi: Latest manufacturing PMI reading.
        inflation: Year-over-year CPI inflation as percentage.
        gdp_growth: Year-over-year real GDP growth as percentage.

    Returns:
        Regime classification string.
    """
    if gdp_growth > 2 and inflation < 3 and pmi > 50:
        return "Goldilocks (strong growth, low inflation)"
    elif gdp_growth > 2 and inflation > 3:
        return "Overheating (strong growth, high inflation)"
    elif gdp_growth < 1 and inflation > 3:
        return "Stagflation (weak growth, high inflation)"
    elif gdp_growth < 1 and inflation < 2:
        return "Deflation risk (weak growth, low inflation)"
    elif yield_slope < 0:
        return "Recession warning (inverted yield curve)"
    elif pmi < 50 and gdp_growth < 2:
        return "Slowdown (contracting PMI, below-trend growth)"
    else:
        return "Mid-cycle (moderate growth)"


def inflation_adjusted_return(
    nominal_return: float, inflation_rate: float
) -> float:
    """Calculate inflation-adjusted (real) return.

    Args:
        nominal_return: Nominal return as percentage.
        inflation_rate: Inflation rate as percentage.

    Returns:
        Real return as percentage.
    """
    return ((1 + nominal_return / 100) / (1 + inflation_rate / 100) - 1) * 100

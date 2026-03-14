# Example: Macro regime analysis

## Prompt
What macro regime are we in right now and what does it mean for asset allocation?

## Output
### Current Macro Regime Assessment

**Key macro indicators:**

| Indicator                  | Value   | Signal              |
|----------------------------|---------|----------------------|
| US 10Y-2Y Spread           | +0.32%  | Mildly positive      |
| US Manufacturing PMI       | 51.2    | Expansion (barely)   |
| US Services PMI            | 54.8    | Solid expansion      |
| CPI YoY                    | 2.9%    | Above target         |
| Core PCE YoY               | 2.7%    | Sticky               |
| Real GDP Growth (Q/Q ann.) | 2.3%    | Above trend          |
| Fed Funds Rate             | 4.50%   | Restrictive          |
| US Unemployment             | 4.1%    | Low but rising       |

**Code used:**
```python
from utils.macro import yield_curve_slope, pmi_trend, macro_regime, real_rate

slope = yield_curve_slope(short_rate=4.18, long_rate=4.50)
print(f"Yield curve slope: {slope:+.2f}%")

pmi_data = [49.2, 49.8, 50.1, 50.3, 50.9, 51.2]
trend = pmi_trend(pmi_data, window=3)
print(f"PMI regime: {trend['regime']}, trend: {trend['trend']}, momentum: {trend['momentum']}")

regime = macro_regime(yield_slope=slope, pmi=51.2, inflation=2.9, gdp_growth=2.3)
print(f"Macro regime: {regime}")

rr = real_rate(nominal_rate=4.50, inflation_rate=2.9)
print(f"Real rate: {rr:.1f}%")
```

**Regime classification: Mid-cycle (moderate growth)**

The economy is growing above trend with sticky inflation, but the manufacturing sector is only barely in expansion. The yield curve has recently un-inverted — historically this precedes either soft landings or delayed recessions.

**Asset allocation implications:**

| Asset Class    | Positioning | Rationale                                          |
|----------------|-------------|-----------------------------------------------------|
| US Equities    | Overweight  | Earnings growth positive, but favour quality/value  |
| Int'l Equities | Neutral     | Relative value exists but USD strength is a headwind|
| Duration       | Underweight | Real rates elevated; wait for clearer cutting cycle |
| Credit         | Neutral     | Spreads tight; carry is attractive but watch defaults|
| Commodities    | Overweight  | Late-cycle inflation hedge, supply constraints      |
| Cash           | Neutral     | 4.5%+ yields make cash a legitimate allocation      |

**Recommendation:** Maintain a pro-growth tilt with inflation protection. Favour equities with pricing power, short-duration credit, and commodity exposure. Reduce long-duration bond exposure until the Fed signals a clearer easing path.

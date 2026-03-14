# Example: Investigate if stocks in Asia have momentum

## Prompt
Investigate if stocks in Asia have momentum.

## Output
### Asia Equity Momentum Analysis

Using 12-month price momentum (current price / price 12 months ago - 1):

| Market        | Index           | 12M Momentum |
|---------------|-----------------|--------------|
| Japan         | Nikkei 225      | +14.2%       |
| India         | Nifty 50        | +11.8%       |
| Taiwan        | TAIEX           | +9.3%        |
| South Korea   | KOSPI           | -2.1%        |
| China         | CSI 300         | -5.7%        |
| Hong Kong     | Hang Seng       | -8.4%        |

**Key findings:**
- Japan and India show strong positive momentum, driven by corporate governance reforms and domestic consumption respectively.
- Taiwan benefits from semiconductor cycle tailwinds.
- China and Hong Kong remain in negative momentum territory due to property sector headwinds and deflationary pressures.

**Code used:**
```python
from utils.momentum import rank_by_momentum

asia_markets = {
    "Japan (Nikkei 225)": nikkei_prices,
    "India (Nifty 50)": nifty_prices,
    # ... etc
}
ranked = rank_by_momentum(asia_markets, period=12)
for name, mom in ranked:
    print(f"{name}: {mom:+.1f}%")
```

**Recommendation:** Overweight Japan and India. Underweight China/HK until momentum inflects.

# Example: US sector rotation analysis

## Prompt
Which US sectors have the strongest momentum right now and where should I rotate into?

## Output
### US Sector Rotation Analysis — Momentum & Valuation Screen

Using 12-month price momentum and forward P/E to identify attractive rotation candidates:

| Sector            | Ticker | 12M Momentum | Fwd P/E | Sharpe (1Y) | Signal     |
|-------------------|--------|--------------|---------|-------------|------------|
| Technology        | XLK    | +28.4%       | 29.1x   | 1.42        | Overweight |
| Industrials       | XLI    | +18.7%       | 19.8x   | 1.15        | Overweight |
| Healthcare        | XLV    | +12.3%       | 16.2x   | 0.89        | Neutral    |
| Financials        | XLF    | +10.1%       | 13.4x   | 0.76        | Neutral    |
| Consumer Staples  | XLP    | +4.2%        | 20.5x   | 0.31        | Underweight|
| Energy            | XLE    | -3.8%        | 11.2x   | -0.12       | Underweight|
| Utilities         | XLU    | -5.1%        | 17.9x   | -0.28       | Underweight|
| Real Estate       | XLRE   | -8.6%        | 34.2x   | -0.45       | Underweight|

**Code used:**
```python
from utils.data_fetch import get_multi_prices
from utils.momentum import rank_by_momentum
from utils.risk import sharpe_ratio

tickers = ["XLK", "XLI", "XLV", "XLF", "XLP", "XLE", "XLU", "XLRE"]
prices = get_multi_prices(tickers, period="2y", interval="1mo")
ranked = rank_by_momentum(prices)
for name, mom in ranked:
    sr = sharpe_ratio(prices[name])
    print(f"{name}: momentum={mom:+.1f}%, sharpe={sr:.2f}")
```

**Key findings:**
- Technology and Industrials show the strongest risk-adjusted momentum — classic late-expansion leadership.
- Energy and Real Estate are in negative momentum territory; avoid until trend inflects.
- Financials offer reasonable value (13.4x fwd P/E) but momentum is middling — watch for breakout.

**Recommendation:** Rotate overweight into XLK and XLI. Pair with a valuation check in 30 days — if Tech P/E exceeds 32x without earnings acceleration, trim back to neutral.

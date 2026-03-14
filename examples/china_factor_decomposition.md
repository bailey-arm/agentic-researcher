# Example: Chinese equity factor decomposition

## Prompt
Help me analyse factor PnL attribution and risks on my portfolio of 100% long BYD.

## Output
I'll run a factor decomposition on your BYD portfolio using our Chinese equity factor model and launch the interactive app so you can explore further.

**Step 1 — run inline analysis:**
```python
from utils.chinalpha import factor_decomposition

# BYD is sz.002594 (Shenzhen-listed)
portfolio = {"sz.002594": 1.0}
result = factor_decomposition(portfolio)
```

**Step 2 — launch interactive app:**
```python
from utils.chinalpha import launch_factor_app

launch_factor_app({"sz.002594": 1.0})
```

### Results

**Portfolio: BYD (比亚迪) — 100% long, Auto Manufacturing sector**

| Category | Ann. Return | Ann. Vol | Sharpe | Var Contribution |
|----------|------------|----------|--------|-----------------|
| MARKET   | +9.5%      | 12.8%    | +0.74  | 14.1%           |
| SECTOR   | +140.6%    | 103.8%   | +1.35  | 46.9%           |
| STYLE    | -14.5%     | 8.4%     | -1.73  | 1.0%            |
| IDIO     | -106.4%    | 103.4%   | -1.03  | 38.1%           |

**Key findings:**
- **SECTOR dominates** (46.9% of variance) — BYD's returns are largely driven by the auto manufacturing sector factor
- **MARKET exposure** contributes 14.1% of variance with positive beta as expected for a single stock
- **SMB (size) loading is negative** (-17.8% return contribution) — BYD is a large-cap, so it has negative exposure to the small-minus-big factor
- **Idiosyncratic risk is high** (38.1% of variance) — expected for a single-stock portfolio

I've also launched the interactive factor decomposition app at http://localhost:8050 with your BYD portfolio pre-loaded. You can:
- Click "Run decomposition" to see interactive Plotly charts
- Add more stocks to the portfolio
- Upload a CSV with your full portfolio
- Upload a custom factor return series

## Prompt
Can you help me do factor decomposition on my portfolio? I'm long Moutai and short China Construction Bank.

## Output
I'll decompose your long Moutai / short CCB portfolio.

**Step 1 — find codes and run decomposition:**
```python
from utils.chinalpha import factor_decomposition, list_stocks

# Find the exact codes
list_stocks("茅台")   # sh.600519
list_stocks("建设银行") # sh.601939

portfolio = {
    "sh.600519": 1.0,   # long 100% Moutai
    "sh.601939": -1.0,  # short 100% China Construction Bank
}

result = factor_decomposition(portfolio)
```

**Step 2 — launch interactive app:**
```python
from utils.chinalpha import launch_factor_app

launch_factor_app({
    "sh.600519": 1.0,
    "sh.601939": -1.0,
})
```

I've run the decomposition and launched the interactive app at http://localhost:8050. The portfolio is market-neutral by construction (long 1, short 1), so MARKET variance contribution should be near zero — the return is dominated by the sector spread (consumer staples vs banking) and idiosyncratic risk.

# Example: Chinese equity factor decomposition

## Prompt
Help me analyse factor PnL attribution and risks on my portfolio of 100% long BYD.

## Output
I'll run a factor decomposition on your BYD portfolio using our Chinese equity factor model.

```python
from utils.chinalpha import factor_decomposition

# BYD is sz.002594 (Shenzhen-listed)
result = factor_decomposition({"sz.002594": 1.0})
```

This runs the full analysis, produces charts, and launches an interactive Dash app at http://localhost:8050 where you can explore further, add stocks, upload CSVs, or add custom factors.

## Prompt
Can you help me do factor decomposition on my portfolio? I'm long Moutai and short China Construction Bank.

## Output
I'll decompose your long Moutai / short CCB portfolio.

```python
from utils.chinalpha import factor_decomposition, list_stocks

# Find the exact codes
list_stocks("茅台")   # sh.600519
list_stocks("建设银行") # sh.601939

result = factor_decomposition({
    "sh.600519": 1.0,   # long 100% Moutai
    "sh.601939": -1.0,  # short 100% CCB
})
```

The decomposition runs inline with charts, and the interactive app is available at http://localhost:8050 with your portfolio pre-loaded.

"""
chinalpha.py
------------
Bridge to the chinalpha research codebase for Chinese equity analysis.

Provides high-level functions the agent can call directly via run_python
to answer questions about Chinese equity portfolios:

  - factor_decomposition(portfolio) — full factor decomposition with charts
  - load_stock_returns(codes)       — get daily returns for specific stocks
  - list_stocks(query)              — search for stock codes by name
  - get_version()                   — chinalpha project version

Example usage in run_python:
    from utils.chinalpha import factor_decomposition
    factor_decomposition({"sz.002594": 1.0})  # long 100% BYD

The chinalpha repo must be available at CHINALPHA_PATH (default: /Users/admin/chinalpha).
"""

import sys
import os
import tomllib
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────────

CHINALPHA_PATH = Path(os.environ.get(
    "CHINALPHA_PATH", "/Users/admin/chinalpha"
))
TOML_PATH = CHINALPHA_PATH / "chinalpha.toml"

# Ensure chinalpha is importable
_repo_str = str(CHINALPHA_PATH)
if _repo_str not in sys.path:
    sys.path.insert(0, _repo_str)


# ── Lazy-loaded shared state ─────────────────────────────────────────

_RETURNS = None
_VOLUME = None
_SECTOR_MAP = None
_SECTOR_DF = None
_UNIVERSE = None


def _ensure_data():
    """Load market data on first use."""
    global _RETURNS, _VOLUME, _SECTOR_MAP, _SECTOR_DF
    if _RETURNS is not None:
        return
    import data_fetch.utils as data_utils
    print("Loading A-share market data (5000+ stocks, 2010–2024)...")
    df = data_utils.load_parquet()
    _RETURNS = data_utils.load_col_data(df, "pctChg") / 100
    _VOLUME = data_utils.load_col_data(df, "amount")
    _SECTOR_DF = data_utils.load_sector()
    _SECTOR_MAP = _SECTOR_DF["sector"]
    print(f"Loaded: {_RETURNS.shape[0]} days × {_RETURNS.shape[1]} stocks")


def _ensure_universe():
    """Build factor universe on first use."""
    global _UNIVERSE
    if _UNIVERSE is not None:
        return _UNIVERSE
    _ensure_data()
    from backtester.factors import FactorUniverse, build_all
    print("Building factor universe (MARKET + SECTOR + STYLE)...")
    factors = build_all(_RETURNS, sector_map=_SECTOR_MAP, volume=_VOLUME)
    _UNIVERSE = FactorUniverse()
    _UNIVERSE.add_factors(factors)
    _UNIVERSE.set_stock_returns(_RETURNS)
    print("Estimating factor loadings (OLS, 252d window)...")
    _UNIVERSE.estimate_loadings(window=252)
    print(f"Ready: {_UNIVERSE.n_factors} factors")
    return _UNIVERSE


# ── High-level API ───────────────────────────────────────────────────

def factor_decomposition(
    portfolio: dict[str, float],
    window: int = 252,
    plot: bool = True,
) -> dict:
    """Run full factor decomposition on a portfolio.

    Parameters
    ----------
    portfolio : dict
        Stock code → weight mapping.
        Codes use baostock format: "sz.002594" (BYD), "sh.600519" (Moutai).
        Positive weight = long, negative = short.
        Example: {"sz.002594": 1.0} means long 100% in BYD.
    window : int
        Loading estimation window in trading days (default 252 = 1 year).
    plot : bool
        If True, produce matplotlib charts (cumulative decomposition,
        variance breakdown, style subfactors).

    Returns
    -------
    dict with keys:
        category_summary  — DataFrame (category × metrics)
        factor_summary    — DataFrame (factor × metrics)
        portfolio_return  — annualised portfolio return
        portfolio_vol     — annualised portfolio volatility
        decomp            — raw FactorDecomposition object
    """
    import numpy as np
    import pandas as pd
    from backtester.factors import decompose_portfolio

    _ensure_data()
    universe = _ensure_universe()

    # Validate codes
    valid = {c: w for c, w in portfolio.items() if c in _RETURNS.columns}
    invalid = set(portfolio) - set(valid)
    if invalid:
        print(f"Warning: codes not found in universe (skipped): {invalid}")
        # Try to help with common format issues
        for code in invalid:
            suggestions = [c for c in _RETURNS.columns if code.replace(".", "") in c.replace(".", "")]
            if suggestions:
                print(f"  Did you mean: {suggestions[:3]}?")
    if not valid:
        print("ERROR: No valid stock codes found.")
        print("Use baostock format: sz.002594 (Shenzhen) or sh.600519 (Shanghai)")
        print(f"Example codes: {list(_RETURNS.columns[:5])}")
        return {}

    # Build weight matrix
    w_df = pd.DataFrame(0.0, index=_RETURNS.index, columns=_RETURNS.columns)
    for code, w in valid.items():
        w_df[code] = w

    # Print portfolio info
    print(f"\nPortfolio: {len(valid)} stocks")
    for code, w in valid.items():
        name = _SECTOR_DF["name"].get(code, "?")
        sector = _SECTOR_MAP.get(code, "?")
        print(f"  {code} ({name}) [{sector}]: {w:+.1%}")
    print(f"  Net weight: {sum(valid.values()):+.3f}")

    # Decompose
    print("\nRunning factor decomposition...")
    decomp = decompose_portfolio(w_df, _RETURNS, universe, loading_window=window)

    # Category summary
    cat_summ = decomp.category_summary()
    print("\n" + "=" * 60)
    print("CATEGORY-LEVEL DECOMPOSITION")
    print("=" * 60)
    for idx, row in cat_summ.iterrows():
        print(f"  {idx:10s}  ret={row.ann_return:+7.2%}  vol={row.ann_vol:6.2%}  "
              f"SR={row.sharpe:+.2f}  var%={row.var_contribution:+6.1%}")

    # Factor-level summary (market + style only)
    full_summ = decomp.summary()
    mask = full_summ["category"].isin(["MARKET", "STYLE", "Alpha", "IDIO"])
    print("\n" + "=" * 60)
    print("FACTOR-LEVEL DECOMPOSITION (MARKET + STYLE)")
    print("=" * 60)
    for idx, row in full_summ.loc[mask].iterrows():
        print(f"  {idx:20s} [{row.category:6s}]  ret={row.ann_return:+7.2%}  "
              f"vol={row.ann_vol:6.2%}  SR={row.sharpe:+.2f}  "
              f"var%={row.var_contribution:+6.1%}")

    # Portfolio-level stats
    port_ret = decomp.portfolio_returns
    ann_ret = port_ret.mean() * 252
    ann_vol = port_ret.std() * np.sqrt(252)
    sharpe = ann_ret / ann_vol if ann_vol > 1e-10 else np.nan
    cum = (1 + port_ret).cumprod()
    mdd = float((cum / cum.cummax() - 1).min())

    print(f"\nPORTFOLIO SUMMARY")
    print(f"  Ann. return:  {ann_ret:+.2%}")
    print(f"  Ann. vol:     {ann_vol:.2%}")
    print(f"  Sharpe:       {sharpe:+.2f}")
    print(f"  Max drawdown: {mdd:.1%}")
    print(f"  Period:       {port_ret.index.min().date()} → {port_ret.index.max().date()}")

    # Plot
    if plot:
        _plot_decomposition(decomp, universe, portfolio)

    return {
        "category_summary": cat_summ,
        "factor_summary": full_summ.loc[mask],
        "portfolio_return": ann_ret,
        "portfolio_vol": ann_vol,
        "portfolio_sharpe": sharpe,
        "max_drawdown": mdd,
        "decomp": decomp,
    }


def _plot_decomposition(decomp, universe, portfolio):
    """Generate decomposition charts."""
    import matplotlib.pyplot as plt
    import numpy as np
    from backtester.factors import FactorCategory

    colors = {"MARKET": "#3b82f6", "SECTOR": "#f97316", "STYLE": "#22c55e",
              "ALPHA": "#a855f7", "IDIO": "#6b7280"}

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))

    # 1. Cumulative return by category
    ax = axes[0, 0]
    cc = decomp.category_contributions
    for col in cc.columns:
        ax.plot(cc[col].cumsum(), label=col,
                color=colors.get(col, "black"), lw=1.2)
    ax.plot(decomp.portfolio_returns.cumsum(), label="TOTAL",
            color="black", lw=2, ls="--")
    ax.axhline(0, color="gray", lw=0.5)
    ax.set_title("Cumulative return by factor category")
    ax.set_ylabel("Cumulative return")
    ax.legend(fontsize=8)

    # 2. Variance contribution
    ax = axes[0, 1]
    cat_summ = decomp.category_summary()
    bar_colors = [colors.get(c, "gray") for c in cat_summ.index]
    ax.bar(cat_summ.index, cat_summ["var_contribution"] * 100,
           color=bar_colors, edgecolor="black", alpha=0.8)
    ax.axhline(0, color="black", lw=0.5)
    ax.set_ylabel("Variance contribution (%)")
    ax.set_title("Variance decomposition")

    # 3. Style subfactor breakdown
    ax = axes[1, 0]
    style_keys = [f.key for f in universe.by_category(FactorCategory.STYLE)]
    for key in style_keys:
        if key in decomp.factor_contributions.columns:
            ax.plot(decomp.factor_contributions[key].cumsum(),
                    label=key.split("/")[-1], lw=1.2)
    ax.axhline(0, color="gray", lw=0.5)
    ax.set_title("STYLE subfactor contributions")
    ax.set_ylabel("Cumulative return")
    ax.legend(fontsize=8)

    # 4. Drawdown
    ax = axes[1, 1]
    cum = (1 + decomp.portfolio_returns).cumprod()
    dd = (cum / cum.cummax() - 1) * 100
    ax.fill_between(dd.index, dd, 0, color="tab:red", alpha=0.4)
    ax.set_title("Portfolio drawdown")
    ax.set_ylabel("Drawdown (%)")
    ax.set_ylim(dd.min() * 1.1, 2)

    codes_str = ", ".join(f"{c} ({w:+.0%})" for c, w in list(portfolio.items())[:5])
    if len(portfolio) > 5:
        codes_str += f" + {len(portfolio) - 5} more"
    fig.suptitle(f"Factor Decomposition: {codes_str}", fontsize=12, y=1.01)
    plt.tight_layout()
    plt.savefig(__chart_path__, dpi=150, bbox_inches="tight") if "__chart_path__" in dir() else None
    plt.show()


def list_stocks(query: str, n: int = 10) -> list[dict]:
    """Search for stock codes by name (Chinese or pinyin substring).

    Parameters
    ----------
    query : str
        Substring to search in stock names, e.g. "比亚迪", "茅台", "bank".
    n : int
        Max results to return.

    Returns
    -------
    List of dicts with keys: code, name, sector.
    """
    _ensure_data()
    matches = []
    query_lower = query.lower()
    for code in _SECTOR_DF.index:
        name = _SECTOR_DF.loc[code, "name"]
        if query_lower in str(name).lower() or query_lower in code.lower():
            matches.append({
                "code": code,
                "name": name,
                "sector": _SECTOR_MAP.get(code, "?"),
            })
            if len(matches) >= n:
                break
    for m in matches:
        print(f"  {m['code']:12s}  {m['name']:10s}  [{m['sector']}]")
    return matches


def load_stock_returns(codes: list[str]) -> "pd.DataFrame":
    """Load daily returns for specific stock codes.

    Parameters
    ----------
    codes : list[str]
        Baostock-format codes, e.g. ["sz.002594", "sh.600519"].

    Returns
    -------
    DataFrame (date × code) of daily simple returns.
    """
    _ensure_data()
    import pandas as pd
    valid = [c for c in codes if c in _RETURNS.columns]
    if not valid:
        print(f"No valid codes found. Example format: {list(_RETURNS.columns[:3])}")
        return pd.DataFrame()
    return _RETURNS[valid]


def load_manifest() -> dict:
    """Load the chinalpha.toml manifest."""
    if not TOML_PATH.exists():
        raise FileNotFoundError(f"chinalpha.toml not found at {TOML_PATH}")
    with open(TOML_PATH, "rb") as f:
        return tomllib.load(f)


def get_version() -> str:
    """Return the chinalpha project version."""
    manifest = load_manifest()
    return manifest.get("project", {}).get("version", "unknown")

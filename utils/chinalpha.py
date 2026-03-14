"""
chinalpha.py
------------
Bridge to the chinalpha research codebase.

Reads chinalpha.toml to discover available apps and modules,
and provides functions to launch them or import their capabilities.

The agent can use these functions when users ask about:
- Factor decomposition / analysis of Chinese equity portfolios
- Hedge portfolio construction and backtesting
- A-share data, indices (CSI 300/1000), sectors, margin data
"""

import subprocess
import sys
import time
import tomllib
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────────

# Path to chinalpha repo — override with CHINALPHA_PATH env var
import os
CHINALPHA_PATH = Path(os.environ.get(
    "CHINALPHA_PATH", "/Users/admin/chinalpha"
))
TOML_PATH = CHINALPHA_PATH / "chinalpha.toml"


def load_manifest() -> dict:
    """Load the chinalpha.toml manifest.

    Returns the full parsed TOML as a dict. Raises FileNotFoundError
    if the manifest is missing.
    """
    if not TOML_PATH.exists():
        raise FileNotFoundError(
            f"chinalpha.toml not found at {TOML_PATH}. "
            f"Set CHINALPHA_PATH env var to the repo root."
        )
    with open(TOML_PATH, "rb") as f:
        return tomllib.load(f)


def list_apps() -> list[dict]:
    """List all available apps from chinalpha.

    Returns a list of dicts with keys: key, name, description, type,
    command, default_port.
    """
    manifest = load_manifest()
    apps = []
    for key, app_cfg in manifest.get("apps", {}).items():
        apps.append({
            "key": key,
            "name": app_cfg.get("name", key),
            "description": app_cfg.get("description", "").strip(),
            "type": app_cfg.get("type", "unknown"),
            "command": app_cfg.get("command", ""),
            "default_port": app_cfg.get("default_port", 8050),
            "example_prompts": app_cfg.get("examples", {}).get("prompts", []),
        })
    return apps


def launch_app(app_key: str, port: int | None = None) -> dict:
    """Launch a chinalpha app by key.

    Parameters
    ----------
    app_key : str
        Key from chinalpha.toml [apps.<key>], e.g. "factor_decomposition".
    port : int, optional
        Port to serve on. Defaults to the app's default_port.

    Returns
    -------
    dict with keys: url, pid, app_key, status.
    """
    manifest = load_manifest()
    app_cfg = manifest.get("apps", {}).get(app_key)
    if app_cfg is None:
        available = list(manifest.get("apps", {}).keys())
        raise ValueError(
            f"App '{app_key}' not found. Available: {available}"
        )

    port = port or app_cfg.get("default_port", 8050)
    command = app_cfg["command"].format(port=port)

    proc = subprocess.Popen(
        command.split(),
        cwd=str(CHINALPHA_PATH),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Give it a moment to start
    time.sleep(2)

    if proc.poll() is not None:
        stderr = proc.stderr.read().decode() if proc.stderr else ""
        return {
            "url": None,
            "pid": None,
            "app_key": app_key,
            "status": f"Failed to start: {stderr[:500]}",
        }

    url = f"http://localhost:{port}"
    return {
        "url": url,
        "pid": proc.pid,
        "app_key": app_key,
        "status": f"Running at {url}",
    }


def get_app_info(app_key: str) -> str:
    """Get a human-readable description of an app's capabilities.

    Useful for the agent to explain what an app can do before launching.
    """
    manifest = load_manifest()
    app_cfg = manifest.get("apps", {}).get(app_key, {})

    lines = [
        f"## {app_cfg.get('name', app_key)}",
        "",
        app_cfg.get("description", "No description.").strip(),
        "",
    ]

    caps = app_cfg.get("capabilities", {})
    if caps:
        lines.append("**Capabilities:**")
        for k, v in caps.items():
            lines.append(f"  - {k}: {v}")
        lines.append("")

    examples = app_cfg.get("examples", {}).get("prompts", [])
    if examples:
        lines.append("**Example queries:**")
        for ex in examples:
            lines.append(f'  - "{ex}"')

    return "\n".join(lines)


def get_version() -> str:
    """Return the chinalpha project version from the manifest."""
    manifest = load_manifest()
    return manifest.get("project", {}).get("version", "unknown")


# ── Direct imports (for run_python use) ──────────────────────────────

def setup_imports():
    """Add chinalpha to sys.path so its modules can be imported.

    After calling this, you can do:
        from backtester.factors import FactorUniverse, decompose_portfolio
        import data_fetch.utils as data_utils
    """
    repo_str = str(CHINALPHA_PATH)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)
    return f"chinalpha ({CHINALPHA_PATH}) added to sys.path"

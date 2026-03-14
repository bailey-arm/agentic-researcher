"""Simple agentic researcher chatbot.

Pairs a user's research prompt with internal utils code and example
prompt-output pairs, then sends everything to Claude for a response.
Claude can execute Python code using the utils/ modules via tool use.
Streams responses for real-time output.
"""

import base64
import json
import os
import glob
import io
import re
import sys
import traceback
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

import anthropic
import gradio as gr

from utils.email_sender import send_research_email

# Configurable model via RESEARCHER_MODEL env var
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
MODEL = os.environ.get("RESEARCHER_MODEL", DEFAULT_MODEL)

# Directory where charts are saved
CHART_DIR = "output/charts"


def load_utils() -> str:
    """Load all Python files from utils/ into a single string."""
    code_blocks = []
    for filepath in sorted(glob.glob("utils/*.py")):
        if filepath.endswith("__init__.py"):
            continue
        with open(filepath) as f:
            code = f.read()
        code_blocks.append(f"### {filepath}\n```python\n{code}\n```")
    return "\n\n".join(code_blocks)


def load_examples() -> str:
    """Load all example files from examples/ into a single string."""
    examples = []
    for filepath in sorted(glob.glob("examples/*.md")):
        with open(filepath) as f:
            content = f.read()
        examples.append(content)
    return "\n\n---\n\n".join(examples)


def run_python(code: str) -> tuple[str, list[str]]:
    """Execute Python code in a sandboxed namespace with access to utils/.

    Returns:
        Tuple of (stdout output, list of chart file paths).
    """
    os.makedirs(CHART_DIR, exist_ok=True)
    stdout_capture = io.StringIO()
    namespace = {"__builtins__": __builtins__}

    # Pre-import all utils modules so Claude's code can use them
    for filepath in sorted(glob.glob("utils/*.py")):
        if filepath.endswith("__init__.py"):
            continue
        module_name = os.path.splitext(os.path.basename(filepath))[0]
        full_module = f"utils.{module_name}"
        try:
            import importlib
            namespace[full_module.replace(".", "_")] = importlib.import_module(full_module)
        except Exception:
            pass

    # Detect charts saved by matplotlib
    charts_before = set(glob.glob(f"{CHART_DIR}/*.png"))

    old_stdout = sys.stdout
    sys.stdout = stdout_capture
    try:
        # Inject a default chart save path so plt.savefig() works easily
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        chart_path = os.path.join(CHART_DIR, f"chart_{timestamp}.png")
        namespace["__chart_path__"] = chart_path

        exec(code, namespace)

        # If matplotlib was used and figures exist, save automatically
        if "matplotlib" in sys.modules or "plt" in namespace:
            try:
                import matplotlib.pyplot as plt
                if plt.get_fignums():
                    plt.savefig(chart_path, dpi=150, bbox_inches="tight")
                    plt.close("all")
            except Exception:
                pass
    except Exception:
        traceback.print_exc(file=stdout_capture)
    finally:
        sys.stdout = old_stdout

    charts_after = set(glob.glob(f"{CHART_DIR}/*.png"))
    new_charts = sorted(charts_after - charts_before)

    return stdout_capture.getvalue() or "(no output)", new_charts


TOOL_DEFINITION = {
    "name": "run_python",
    "description": (
        "Execute Python code. The utils/ package is available for import "
        "(e.g. `from utils.momentum import rank_by_momentum`, "
        "`from utils.data_fetch import get_prices`, "
        "`from utils.chinalpha import factor_decomposition, launch_factor_app`). "
        "Use print() to produce output. For charts, use matplotlib and call "
        "plt.savefig(__chart_path__) or just plt.show() — charts are saved "
        "automatically. For Chinese equity portfolio analysis, use utils.chinalpha "
        "which provides factor decomposition and an interactive Dash app. "
        "Only use this tool when computation would add value."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python code to execute. Use print() for output.",
            }
        },
        "required": ["code"],
    },
}


def build_system_prompt(utils_code: str, examples: str) -> str:
    return f"""You are a research analyst assistant. You help investigate financial and economic research questions.

You have access to the following internal utility code that you can import and run:

{utils_code}

Here are examples of previous research outputs. Match this style and depth:

{examples}

Instructions:
- Use the run_python tool to actually execute code when computation adds value.
- Import from utils/ in your code (e.g. `from utils.momentum import rank_by_momentum`).
- Use `from utils.data_fetch import get_prices, get_multi_prices` to fetch real market data.
- For charts, use matplotlib. Call plt.savefig(__chart_path__) to save, or just plt.show().
- Be specific with data and findings.
- Structure your output with clear headers, tables where appropriate, and a recommendation.
- After running code, incorporate the results into your final written analysis.
- You have full conversation history — refer back to prior analysis when the user asks follow-ups."""


def save_output(prompt: str, response: str, code_runs: list) -> str:
    """Save the prompt, response, and any code executions to output/ as JSON."""
    os.makedirs("output", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = "_".join(prompt.lower().split()[:6])
    slug = "".join(c for c in slug if c.isalnum() or c == "_")[:50]
    filename = f"{timestamp}_{slug}.json"
    filepath = os.path.join("output", filename)

    data = {
        "timestamp": datetime.now().isoformat(),
        "prompt": prompt,
        "response": response,
        "code_runs": code_runs,
    }
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    return filepath


def history_to_messages(history: list[dict]) -> list[dict]:
    """Convert Gradio chat history to Claude API messages format.

    Gradio's messages format provides history as a list of
    {"role": ..., "content": ...} dicts.
    """
    messages = []
    for msg in history:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role in ("user", "assistant") and content:
            # Strip any image markdown from assistant messages before sending back
            clean = re.sub(r"\n*!\[.*?\]\(.*?\)", "", content).strip()
            if clean:
                messages.append({"role": role, "content": clean})
    return messages


def chat(prompt: str, history: list[dict], send_email: bool = False, email_to: str = ""):
    """Send a research prompt to Claude with tool use + streaming."""
    client = anthropic.Anthropic()

    utils_code = load_utils()
    examples = load_examples()
    system = build_system_prompt(utils_code, examples)

    # Build messages from conversation history + current prompt
    messages = history_to_messages(history)
    messages.append({"role": "user", "content": prompt})

    code_runs = []
    all_charts: list[str] = []

    full_response = ""  # Accumulates text across tool-use loops

    while True:
        collected_text = ""
        collected_content = []
        stop_reason = None

        with client.messages.stream(
            model=MODEL,
            max_tokens=4096,
            system=system,
            tools=[TOOL_DEFINITION],
            messages=messages,
        ) as stream:
            for event in stream:
                if event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        collected_text += event.delta.text
                        yield full_response + collected_text

            final_message = stream.get_final_message()
            stop_reason = final_message.stop_reason
            collected_content = final_message.content

        if stop_reason == "tool_use":
            full_response += collected_text + "\n\n> ⏳ *Running code...*\n\n"
            yield full_response

            messages.append({"role": "assistant", "content": collected_content})

            tool_results = []
            for block in collected_content:
                if block.type == "tool_use":
                    code = block.input["code"]
                    output, charts = run_python(code)
                    code_runs.append({"code": code, "output": output, "charts": charts})
                    all_charts.extend(charts)

                    result_text = output
                    if charts:
                        result_text += f"\n[Charts saved: {', '.join(charts)}]"

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_text,
                    })

            messages.append({"role": "user", "content": tool_results})
            # Replace the spinner with a checkmark once code finishes
            full_response = full_response.replace(
                "> ⏳ *Running code...*", "> ✅ *Code executed*"
            )
        else:
            final_text = full_response + collected_text

            # Append chart images as base64 data URIs for inline display
            if all_charts:
                chart_md = "\n\n"
                for chart_path in all_charts:
                    abs_path = os.path.abspath(chart_path)
                    if os.path.exists(abs_path):
                        with open(abs_path, "rb") as img_f:
                            b64 = base64.b64encode(img_f.read()).decode()
                        chart_md += f"![Chart](data:image/png;base64,{b64})\n"
                final_text += chart_md

            yield final_text
            save_output(prompt, final_text, code_runs)

            # Send email if requested
            if send_email:
                recipient = email_to.strip() or None
                subject = f"Research: {prompt[:80]}"
                email_body = re.sub(r"\n*!\[.*?\]\(.*?\)", "", final_text).strip()
                status = send_research_email(
                    subject=subject,
                    body_markdown=email_body,
                    chart_paths=all_charts,
                    recipient=recipient,
                )
                final_text += f"\n\n---\n*{status}*"
                yield final_text

            return


dark_theme = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="blue",
    neutral_hue="slate",
    font=gr.themes.GoogleFont("Inter"),
    font_mono=gr.themes.GoogleFont("JetBrains Mono"),
)

CUSTOM_CSS = """
.gradio-container { max-width: 900px !important; margin: auto !important; }
.message-wrap { font-size: 15px !important; }
.bot .message-bubble-border { border: none !important; }
"""


def respond(message, history, send_email, email_to):
    for partial in chat(message, history, send_email, email_to):
        yield partial


with gr.Blocks(theme=dark_theme, css=CUSTOM_CSS, title="Agentic Researcher") as demo:
    gr.Markdown("# Agentic Researcher")

    with gr.Accordion("Email settings", open=False):
        with gr.Row():
            send_email = gr.Checkbox(label="Email results", value=False)
            email_to = gr.Textbox(
                label="Recipient",
                value="bailey.arm.business@gmail.com",
                placeholder="email@example.com",
            )

    gr.ChatInterface(
        fn=respond,
        additional_inputs=[send_email, email_to],
    )

if __name__ == "__main__":
    demo.launch()

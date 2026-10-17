"""
tracing_setup.py
----------------
Tracing for the whole project.

1) LOCAL (always on): prints a readable tree in the console and saves every
   span to traces/trace_log.jsonl. No API key needed.
2) OPENAI DASHBOARD (optional): if OPENAI_API_KEY is set in .env, traces are
   ALSO exported to https://platform.openai.com/traces (the log view the
   instructor showed). The key is used for traces only; the LLM calls still
   go to Groq / Gemini.

Call setup_tracing() once at startup (config.py does it after load_dotenv()).
"""

import json
import os
import threading
from datetime import datetime
from pathlib import Path

from agents.tracing import (
    TracingProcessor,
    add_trace_processor,
    set_trace_processors,
    set_tracing_export_api_key,
)

LOG_DIR = Path("traces")
LOG_FILE = LOG_DIR / "trace_log.jsonl"
MAX_TEXT = 160


def _short(value, limit: int = MAX_TEXT) -> str:
    text = value if isinstance(value, str) else json.dumps(value, default=str, ensure_ascii=False)
    text = text.replace("\n", " ")
    return text if len(text) <= limit else text[:limit] + "..."


def _label(span_data) -> str:
    kind = span_data.type
    if kind in ("agent", "function", "guardrail", "custom"):
        return f"{kind}: {getattr(span_data, 'name', '?')}"
    if kind == "generation":
        return f"model call: {getattr(span_data, 'model', '?')}"
    if kind == "handoff":
        return f"handoff: {getattr(span_data, 'from_agent', '?')} -> {getattr(span_data, 'to_agent', '?')}"
    return kind


def _duration(span) -> str:
    try:
        start = datetime.fromisoformat(span.started_at)
        end = datetime.fromisoformat(span.ended_at)
        return f"{(end - start).total_seconds():.2f}s"
    except Exception:
        return "?"


class ClaimsTraceProcessor(TracingProcessor):
    """Console tree + JSONL file."""

    def __init__(self):
        LOG_DIR.mkdir(exist_ok=True)
        self._depth: dict[str, int] = {}
        self._lock = threading.Lock()

    # ----- helpers -----
    def _print(self, text: str):
        with self._lock:
            print(text, flush=True)

    def _write(self, record: dict):
        with self._lock:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, default=str, ensure_ascii=False) + "\n")

    # ----- trace events -----
    def on_trace_start(self, trace):
        self._print(f"\n=== TRACE START: {trace.name} ===")
        self._write({"event": "trace_start", **trace.export()})

    def on_trace_end(self, trace):
        self._print(f"=== TRACE END: {trace.name} ===\n")
        self._write({"event": "trace_end", **trace.export()})

    # ----- span events -----
    def on_span_start(self, span):
        parent_depth = self._depth.get(span.parent_id, -1) if span.parent_id else -1
        depth = parent_depth + 1
        self._depth[span.span_id] = depth
        self._print(f"{'  ' * depth}> {_label(span.span_data)}")

    def on_span_end(self, span):
        depth = self._depth.pop(span.span_id, 0)
        data = span.span_data
        indent = "  " * depth
        dur = _duration(span)

        if data.type == "function":
            self._print(f"{indent}  tool input : {_short(getattr(data, 'input', ''))}")
            self._print(f"{indent}  tool output: {_short(getattr(data, 'output', ''))}  ({dur})")
        elif data.type == "guardrail":
            self._print(f"{indent}  triggered: {getattr(data, 'triggered', '?')}  ({dur})")
        elif data.type == "generation":
            self._print(f"{indent}  done ({dur})")

        if span.error:
            self._print(f"{indent}  !! ERROR: {_short(span.error)}")

        self._write({"event": "span_end", **span.export()})

    def shutdown(self):
        pass

    def force_flush(self):
        pass


_configured = False


def setup_tracing():
    global _configured
    if _configured:
        return

    local = ClaimsTraceProcessor()
    openai_key = os.getenv("OPENAI_API_KEY")

    if openai_key:
        # Keep the SDK's default exporter (OpenAI dashboard) AND add our local one.
        set_tracing_export_api_key(openai_key)
        add_trace_processor(local)
        print("[tracing] local log + OpenAI dashboard enabled", flush=True)
    else:
        # No key: replace the default exporter so nothing tries to reach OpenAI.
        set_trace_processors([local])
        print("[tracing] local log only (no OPENAI_API_KEY set)", flush=True)

    _configured = True
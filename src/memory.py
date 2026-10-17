"""
memory.py
---------
Conversation memory (SQLiteSession) and shared run context.
"""

from dataclasses import dataclass
from pathlib import Path

from agents import SQLiteSession

DB_PATH = Path("data/sessions.db")


def get_session(session_id: str) -> SQLiteSession:
    """One session_id = one conversation. History is stored on disk."""
    DB_PATH.parent.mkdir(exist_ok=True)
    return SQLiteSession(session_id, str(DB_PATH))


@dataclass
class ClaimContext:
    """Shared state passed to agents/tools via Runner.run(..., context=ctx).
    Not sent to the LLM; only your Python code (tools, guardrails) can read it."""
    session_id: str
    policy_number: str | None = None
    case_id: str | None = None
    escalated: bool = False
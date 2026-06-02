"""In-memory data store — Phase 2.

This is the single shared dictionary that all route handlers read from
and write to. It lives here instead of inside goals.py so that:

  1. The pytest autouse fixture can call clear_all() and genuinely reset
     the data between tests (if store lived in goals.py, it would be a
     different dict object from the one the fixture tries to clear).

  2. Phase 3 only needs to change THIS file (swap dicts for Supabase calls)
     without touching any router file.

Thread safety: FastAPI's TestClient runs requests on threads. Without a
Lock, two concurrent requests could corrupt the dict (e.g., one reads
while another deletes). The Lock makes read-validate-write atomic.
"""

import threading

from lpi.models import Goal, Signal

# ── Goals ──────────────────────────────────────────────────────────────────────
_goals: dict[str, Goal] = {}
_goals_lock = threading.Lock()

# ── Signals ────────────────────────────────────────────────────────────────────
_signals: dict[str, Signal] = {}
_signals_lock = threading.Lock()


def clear_all() -> None:
    """Wipe every in-memory collection. Call ONLY from tests."""
    with _goals_lock:
        _goals.clear()
    with _signals_lock:
        _signals.clear()

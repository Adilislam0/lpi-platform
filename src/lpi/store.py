"""Supabase-backed store — Phase 2 integration.

Replaces the in-memory dict from Phase 1 stub.
goals.py and signals.py are untouched — they still call the same
functions, but now data persists in Supabase.

For tests: set SUPABASE_URL / SUPABASE_KEY in the local .env that
points to your local Supabase instance. clear_all() truncates rows
in the goals table between test runs.
"""

import threading
from typing import TYPE_CHECKING, cast

from lpi.config import settings
from lpi.models import Goal, Signal

if TYPE_CHECKING:
    from supabase import Client  # type: ignore[attr-defined]


def _get_client() -> "Client":
    from supabase import create_client  # type: ignore[attr-defined]
    return create_client(settings.supabase_url, settings.supabase_key)


# ── Keep the lock — still needed for test isolation ───────────────────────────
_goals_lock = threading.Lock()
_signals_lock = threading.Lock()

# ── In-memory signal store ────────────────────────────────────────────────────
# Phase 3 will move this to Supabase. The signals ROUTER (routers/signals.py)
# currently returns HTTP 501 for POST and [] for GET as Phase 3 stubs, so
# insert_signal / get_signal / list_signals below are not yet called by any
# router. They are defined here so the store contract is complete and the
# Phase 3 implementer only needs to wire the router — not add new store fns.
_signals: dict[str, Signal] = {}


# ── Goals ──────────────────────────────────────────────────────────────────────

def get_goal(goal_id: str) -> Goal | None:
    result = _get_client().table("goals").select("*").eq("id", goal_id).execute()
    if not result.data:
        return None
    return Goal(**cast(dict, result.data[0]))


def list_goals(
    user_id: str | None = None,
    smile_phase: str | None = None,
) -> list[Goal]:
    query = _get_client().table("goals").select("*")
    if user_id:
        query = query.eq("user_id", user_id)
    if smile_phase:
        query = query.eq("smile_phase", smile_phase)
    result = query.execute()
    return [Goal(**cast(dict, row)) for row in result.data]


def insert_goal(goal: Goal) -> Goal:
    _get_client().table("goals").insert(goal.model_dump(mode="json")).execute()
    return goal


def update_goal(goal_id: str, updates: dict) -> Goal:
    result = (
        _get_client().table("goals").update(updates).eq("id", goal_id).execute()
    )
    return Goal(**cast(dict, result.data[0]))


def delete_goal(goal_id: str) -> None:
    _get_client().table("goals").delete().eq("id", goal_id).execute()


# ── Signals (in-memory stub — Phase 3 will move to Supabase) ─────────────────

def get_signal(signal_id: str) -> Signal | None:
    return _signals.get(signal_id)


def list_signals(stream: str | None = None) -> list[Signal]:
    if stream:
        return [s for s in _signals.values() if s.stream == stream]
    return list(_signals.values())


def insert_signal(signal: Signal) -> Signal:
    with _signals_lock:
        _signals[signal.id] = signal
    return signal


# ── Test helper ───────────────────────────────────────────────────────────────

def clear_all() -> None:
    """Wipe all data. Call ONLY from tests.

    Deletes all rows from the goals table by filtering on user_id.
    We cannot issue a DELETE with no filter — supabase-py v2 requires
    at least one filter to prevent accidental full-table wipes.

    We use .neq("user_id", "__sentinel_never_exists__") rather than
    .neq("id", "") because `id` is a UUID column and an empty-string
    comparison raises a Postgres type-cast error. `user_id` is TEXT,
    so the sentinel string comparison is safe and always matches every row.
    """
    _get_client().table("goals").delete().neq("user_id", "__sentinel_never_exists__").execute()
    _signals.clear()

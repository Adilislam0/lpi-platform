"""Goal priority scoring — SMILE-weighted composite algorithm.

Owner : Jaivardhan Singh  (Phase 2 — Task C)
QA    : Daksh Garg 

═══════════════════════════════════════════════════════════════════════
WHY THIS FILE EXISTS (AND WHY IT'S SEPARATE FROM goals.py)
═══════════════════════════════════════════════════════════════════════

Scoring is pure math — it takes a Goal object and returns a float.
It has NO knowledge of HTTP, databases, stores, or FastAPI.
Keeping it separate means:

  1. It can be tested with zero server setup (no TestClient needed).
     Just create a Goal object and call score_goal(). Fast, isolated.

  2. Phase 4's recommendation engine imports score_explanation() to
     produce SMILE-grounded reasoning without touching any router code.

  3. If the lead changes the formula (which they might), you edit ONE
     file and all callers (list_goals, recommendation engine, tests)
     automatically use the new logic.

═══════════════════════════════════════════════════════════════════════
THE FORMULA (approved by lead — do not change without lead sign-off)
═══════════════════════════════════════════════════════════════════════

    score = (priority × 0.5) + (smile_phase_weight × 0.3) + (urgency_flag × 0.2)

Three components, three weights that sum to 1.0:

  COMPONENT 1 — priority × 0.5   (50% of score)
    The user's explicit importance rating, 1–10.
    50% weight makes this the DOMINANT signal.
    If you care most about a goal, give it priority 9–10 and it will
    always float near the top regardless of phase or urgency.

  COMPONENT 2 — smile_phase_weight × 0.3   (30% of score)
    Context about WHERE in the SMILE journey this goal is.
    Phase weights are SEQUENTIAL: sense=1, model=2, intervene=3, learn=4, evolve=5.
    Why sequential?
      A goal in EVOLVE has already passed through SENSE, MODEL, INTERVENE,
      and LEARN. It has accumulated work and momentum. Letting it stall now
      wastes all prior effort. Higher phase = higher weight = "don't drop this."
    30% weight: meaningful enough to break ties, small enough to not
    override a legitimately higher-priority lower-phase goal.

  COMPONENT 3 — urgency_flag × 0.2   (20% of score)
    A binary OVERRIDE for time-sensitive situations.
    True = 1 = adds 0.20 to the total score.
    False = 0 = no contribution.
    When to set urgency_flag=True:
      - Deliverable due in the next 24–48 hours
      - Goal suddenly became critical due to external event
      - Meeting with stakeholder where this goal will be reviewed
    20% weight: noticeable in rankings but can't completely override
    priority (a priority-1 urgent goal won't leapfrog a priority-10
    non-urgent goal — the priority difference is too large).

═══════════════════════════════════════════════════════════════════════
SCORE RANGE
═══════════════════════════════════════════════════════════════════════

  Minimum: priority=1, sense, urgent=False
    (1×0.5) + (1×0.3) + (0×0.2) = 0.5 + 0.3 + 0.0 = 0.80

  Maximum: priority=10, evolve, urgent=True
    (10×0.5) + (5×0.3) + (1×0.2) = 5.0 + 1.5 + 0.2 = 6.70

  This is a RANKING score, not a 0–10 display metric.
  Its absolute value matters only relative to other goals' scores.

═══════════════════════════════════════════════════════════════════════
VERIFIED WORKED EXAMPLES (all hand-checked)
═══════════════════════════════════════════════════════════════════════

  p=5,  sense,     urgent=False → (5×0.5)+(1×0.3)+(0×0.2) =  2.80
  p=5,  model,     urgent=False → (5×0.5)+(2×0.3)+(0×0.2) =  3.10
  p=5,  intervene, urgent=False → (5×0.5)+(3×0.3)+(0×0.2) =  3.40
  p=5,  learn,     urgent=False → (5×0.5)+(4×0.3)+(0×0.2) =  3.70
  p=5,  evolve,    urgent=False → (5×0.5)+(5×0.3)+(0×0.2) =  4.00
  p=5,  evolve,    urgent=True  → (5×0.5)+(5×0.3)+(1×0.2) =  4.20
  p=10, evolve,    urgent=True  → (10×0.5)+(5×0.3)+(1×0.2) = 6.70  ← maximum
  p=1,  sense,     urgent=False → (1×0.5)+(1×0.3)+(0×0.2) =  0.80  ← minimum

═══════════════════════════════════════════════════════════════════════
CHANGE FROM PREVIOUS DRAFT (explanation for the team)
═══════════════════════════════════════════════════════════════════════

  The first scoring draft (before lead approval) used:
    (0.60 × priority) + (0.40 × phase_urgency_float × 10)
    with INTERVENE having the highest float weight (1.00).

  The lead's approved formula:
    (0.50 × priority) + (0.30 × sequential_phase_int) + (0.20 × urgency_flag)
    with EVOLVE having the highest integer weight (5).

  Key differences:
    - Priority weight dropped from 0.60 → 0.50 (urgency takes that 0.10)
    - Phase weights changed from float multipliers to sequential integers 1–5
    - EVOLVE is now highest (not INTERVENE) — reflects "don't abandon near-done goals"
    - urgency_flag explicitly participates in the formula
    - Score range changed: [2.6, 10.0] → [0.8, 6.7] (different absolute scale,
      but ranking behaviour is what matters for list_goals ordering)
"""

from lpi.models import Goal, SmilePhase

# ── Formula weights (lead-approved — do not change without sign-off) ──────────

PRIORITY_WEIGHT: float = 0.5    # priority (1–10), 50% of score
PHASE_WEIGHT: float = 0.3       # SMILE phase integer weight (1–5), 30% of score
URGENCY_WEIGHT: float = 0.2     # urgency_flag (0 or 1), 20% of score
# Sanity check: 0.5 + 0.3 + 0.2 = 1.0 — weights sum to exactly 1.

# ── SMILE phase integer weights (sequential — further along = more weight) ────
#
# WHY integers 1–5 instead of floats 0.50–1.00?
#   Sequential integers make the phase contribution linear and predictable.
#   Each phase step adds (0.3 × 1) = 0.30 to the score.
#   With floats, the relationship between phases was non-linear and harder
#   to explain to stakeholders: "why does LEARN score lower than INTERVENE?"
#   With integers: "each phase step adds 0.30 to your goal's score."
#
PHASE_WEIGHTS: dict[SmilePhase, int] = {
    SmilePhase.SENSE: 1,       # You're observing. Score boost: 0.30
    SmilePhase.MODEL: 2,       # You're structuring. Score boost: 0.60
    SmilePhase.INTERVENE: 3,   # You're acting. Score boost: 0.90
    SmilePhase.LEARN: 4,       # You're evaluating. Score boost: 1.20
    SmilePhase.EVOLVE: 5,      # You're scaling. Score boost: 1.50
}


# ── Core scoring function ──────────────────────────────────────────────────────

def score_goal(goal: Goal) -> float:
    """Compute the SMILE-weighted composite priority score for a single goal.

    This is the ONLY place the formula is implemented. Every other module
    that needs a score calls this function — no copy-pasting the formula.

    Args:
        goal: A full Goal object (must have priority, smile_phase, urgency_flag).

    Returns:
        float — composite ranking score, range [0.80, 6.70],
        rounded to 2 decimal places.
        Higher score = surface this goal earlier in sorted lists.

    Formula:
        score = (priority × PRIORITY_WEIGHT)
              + (phase_weight × PHASE_WEIGHT)
              + (urgency × URGENCY_WEIGHT)

    Note on int(urgency_flag):
        Python booleans ARE integers: True == 1, False == 0.
        int(True) = 1, int(False) = 0.
        Multiplying a bool by a float works, but int() makes the intent explicit.
    """
    phase_w = PHASE_WEIGHTS[goal.smile_phase]       # integer 1–5
    urgency = int(goal.urgency_flag)                 # 1 if True, 0 if False

    raw = (
        (goal.priority * PRIORITY_WEIGHT)           # e.g. 5 × 0.5 = 2.50
        + (phase_w * PHASE_WEIGHT)                   # e.g. 3 × 0.3 = 0.90
        + (urgency * URGENCY_WEIGHT)                 # e.g. 1 × 0.2 = 0.20
    )                                                # total:          3.60

    # round to 2 dp for stable equality comparisons in tests
    return round(raw, 2)


# ── Human-readable explanation ─────────────────────────────────────────────────

def score_explanation(goal: Goal) -> str:
    """Return a one-sentence explanation of WHY this goal has its score.

    Used by the Phase 4 recommendation engine to produce reasoning like:
    "Score 3.60: priority 5 × 0.5 = 2.50, INTERVENE phase weight 3 × 0.3 = 0.90,
     urgency True × 0.2 = 0.20. Phase: Taking action, making changes."

    This is what makes LPI recommendations EXPLAINABLE rather than "black box."
    Every recommendation can cite specific score components to justify why
    one goal is prioritised over another.
    """
    from lpi.smile import get_phase_description

    phase_w = PHASE_WEIGHTS[goal.smile_phase]
    urgency = int(goal.urgency_flag)
    s = score_goal(goal)

    # Show each component's contribution separately for transparency
    p_contrib = round(goal.priority * PRIORITY_WEIGHT, 2)
    ph_contrib = round(phase_w * PHASE_WEIGHT, 2)
    u_contrib = round(urgency * URGENCY_WEIGHT, 2)

    return (
        f"Score {s:.2f}: "
        f"priority {goal.priority} × {PRIORITY_WEIGHT} = {p_contrib}, "
        f"phase '{goal.smile_phase}' weight {phase_w} × {PHASE_WEIGHT} = {ph_contrib}, "
        f"urgency {bool(urgency)} × {URGENCY_WEIGHT} = {u_contrib}. "
        f"Phase: {get_phase_description(goal.smile_phase)}."
    )


# ── Sort helper ────────────────────────────────────────────────────────────────

def sort_goals_by_score(goals: list[Goal]) -> list[Goal]:
    """Return a new list of goals sorted by composite score descending.

    Tiebreaker: created_at ascending — if two goals score identically,
    the older (more established) one surfaces first. This prevents the
    sort order from changing arbitrarily when goals have the same score.

    Does NOT mutate the input list (returns a new sorted list).
    The `sorted()` built-in always returns a new list.

    Called by list_goals() in goals.py after all filters are applied:
        goals = sort_goals_by_score(goals)

    Using this instead of goals.sort(key=lambda g: (-g.priority, g.created_at))
    means the sort logic is centralised, tested, and SMILE-aware.
    """
    return sorted(goals, key=lambda g: (-score_goal(g), g.created_at))
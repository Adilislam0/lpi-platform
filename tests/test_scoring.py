"""Tests for the SMILE-weighted goal priority scoring module.

Owner : Jaivardhan Singh
QA    : Ankit Kumar Singh

═══════════════════════════════════════════════════════════════════════
WHY THIS FILE REPLACES THE PREVIOUS test_scoring.py
═══════════════════════════════════════════════════════════════════════

The previous test file tested the DRAFT formula:
    (BASE_WEIGHT × priority) + (PHASE_WEIGHT × phase_urgency_float × 10)
    with BASE_WEIGHT=0.60, PHASE_WEIGHT=0.40

The lead's APPROVED formula is different:
    (priority × 0.5) + (smile_phase_weight × 0.3) + (urgency_flag × 0.2)
    with sequential integer phase weights: sense=1, model=2, ..., evolve=5

Because the formula changed, ALL known-value assertions in the old file
were wrong for the new formula. Rather than patching individual values,
the file is replaced completely so every test reflects the approved spec.

New in this file:
  - TestScoreGoalWithUrgency  — tests urgency_flag's contribution
  - _goal() helper now takes `urgent: bool = False`
  - Known-value tests recomputed for the new formula
  - TestPhaseWeightsConstant  — validates the sequential 1–5 integer weights

Run: pytest tests/test_scoring.py -v
Zero external dependencies — no HTTP, no store, no TestClient needed.
"""

import time
from datetime import UTC, datetime

import pytest

from lpi.models import Goal, SmilePhase
from lpi.scoring import (
    PHASE_WEIGHT,
    PHASE_WEIGHTS,
    PRIORITY_WEIGHT,
    URGENCY_WEIGHT,
    score_explanation,
    score_goal,
    sort_goals_by_score,
)

# ── Helper ────────────────────────────────────────────────────────────────────

def _goal(
    priority: int,
    phase: SmilePhase,
    urgent: bool = False,    # ← TASK C: added urgency_flag parameter
    title: str = "Test",
) -> Goal:
    """Build a minimal Goal for scoring tests.

    No fixtures, no HTTP client, no store — just a plain Python object.
    urgency_flag defaults to False so all old call sites still work
    (backward compatible). Pass urgent=True to test urgent goals.
    """
    now = datetime.now(UTC)
    return Goal(
        id="test-id",
        user_id="default_user",
        title=title,
        description="",
        priority=priority,
        smile_phase=phase,
        urgency_flag=urgent,       # TASK C: pass through to model
        created_at=now,
        updated_at=now,
    )


# ── PHASE_WEIGHTS constant ────────────────────────────────────────────────────

class TestPhaseWeightsConstant:
    """Validate the approved sequential 1–5 integer weights.

    These tests are the contract for the formula. If someone changes
    the PHASE_WEIGHTS dict, these tests fail immediately and visibly
    before any deployment.
    """

    def test_sense_weight_is_1(self) -> None:
        # SENSE is the starting phase — lowest weight
        assert PHASE_WEIGHTS[SmilePhase.SENSE] == 1

    def test_model_weight_is_2(self) -> None:
        assert PHASE_WEIGHTS[SmilePhase.MODEL] == 2

    def test_intervene_weight_is_3(self) -> None:
        assert PHASE_WEIGHTS[SmilePhase.INTERVENE] == 3

    def test_learn_weight_is_4(self) -> None:
        assert PHASE_WEIGHTS[SmilePhase.LEARN] == 4

    def test_evolve_weight_is_5(self) -> None:
        # EVOLVE is furthest along — highest weight (don't abandon near-done goals)
        assert PHASE_WEIGHTS[SmilePhase.EVOLVE] == 5

    def test_all_5_phases_have_weights(self) -> None:
        assert len(PHASE_WEIGHTS) == 5
        for phase in SmilePhase:
            assert phase in PHASE_WEIGHTS, f"Missing weight for {phase}"

    def test_evolve_is_highest_weight(self) -> None:
        assert max(PHASE_WEIGHTS.values()) == PHASE_WEIGHTS[SmilePhase.EVOLVE]

    def test_sense_is_lowest_weight(self) -> None:
        assert min(PHASE_WEIGHTS.values()) == PHASE_WEIGHTS[SmilePhase.SENSE]

    def test_formula_weights_sum_to_1(self) -> None:
        """0.5 + 0.3 + 0.2 must equal exactly 1.0.

        This is a design invariant: the three components account for 100%
        of the score weight. If this fails, someone changed a constant
        without updating the others.
        """
        assert PRIORITY_WEIGHT + PHASE_WEIGHT + URGENCY_WEIGHT == pytest.approx(1.0)

    def test_urgency_weight_is_0_2(self) -> None:
        assert URGENCY_WEIGHT == pytest.approx(0.2)

    def test_priority_weight_is_0_5(self) -> None:
        assert PRIORITY_WEIGHT == pytest.approx(0.5)

    def test_phase_weight_is_0_3(self) -> None:
        assert PHASE_WEIGHT == pytest.approx(0.3)


# ── score_goal — known values (hand-verified) ────────────────────────────────

class TestScoreGoalKnownValues:
    """Every assertion here is hand-computed and independently verified.

    Formula reminder:
        score = (priority × 0.5) + (phase_weight × 0.3) + (urgency_flag × 0.2)

    These are the ground-truth values. If score_goal() returns something
    different, the implementation is wrong — not the test.
    """

    def test_p5_sense_nonurgent(self) -> None:
        """(5×0.5) + (1×0.3) + (0×0.2) = 2.50 + 0.30 + 0.00 = 2.80"""
        assert score_goal(_goal(5, SmilePhase.SENSE, False)) == 2.80

    def test_p5_model_nonurgent(self) -> None:
        """(5×0.5) + (2×0.3) + (0×0.2) = 2.50 + 0.60 + 0.00 = 3.10"""
        assert score_goal(_goal(5, SmilePhase.MODEL, False)) == 3.10

    def test_p5_intervene_nonurgent(self) -> None:
        """(5×0.5) + (3×0.3) + (0×0.2) = 2.50 + 0.90 + 0.00 = 3.40"""
        assert score_goal(_goal(5, SmilePhase.INTERVENE, False)) == 3.40

    def test_p5_learn_nonurgent(self) -> None:
        """(5×0.5) + (4×0.3) + (0×0.2) = 2.50 + 1.20 + 0.00 = 3.70"""
        assert score_goal(_goal(5, SmilePhase.LEARN, False)) == 3.70

    def test_p5_evolve_nonurgent(self) -> None:
        """(5×0.5) + (5×0.3) + (0×0.2) = 2.50 + 1.50 + 0.00 = 4.00"""
        assert score_goal(_goal(5, SmilePhase.EVOLVE, False)) == 4.00

    def test_p5_evolve_urgent(self) -> None:
        """(5×0.5) + (5×0.3) + (1×0.2) = 2.50 + 1.50 + 0.20 = 4.20"""
        assert score_goal(_goal(5, SmilePhase.EVOLVE, True)) == 4.20

    def test_p10_evolve_urgent_is_maximum(self) -> None:
        """(10×0.5) + (5×0.3) + (1×0.2) = 5.00 + 1.50 + 0.20 = 6.70 ← max"""
        assert score_goal(_goal(10, SmilePhase.EVOLVE, True)) == 6.70

    def test_p1_sense_nonurgent_is_minimum(self) -> None:
        """(1×0.5) + (1×0.3) + (0×0.2) = 0.50 + 0.30 + 0.00 = 0.80 ← min"""
        assert score_goal(_goal(1, SmilePhase.SENSE, False)) == 0.80

    def test_p7_sense_nonurgent(self) -> None:
        """(7×0.5) + (1×0.3) + (0×0.2) = 3.50 + 0.30 + 0.00 = 3.80"""
        assert score_goal(_goal(7, SmilePhase.SENSE, False)) == 3.80

    def test_p7_sense_urgent(self) -> None:
        """(7×0.5) + (1×0.3) + (1×0.2) = 3.50 + 0.30 + 0.20 = 4.00"""
        assert score_goal(_goal(7, SmilePhase.SENSE, True)) == 4.00

    def test_p8_intervene_nonurgent(self) -> None:
        """(8×0.5) + (3×0.3) + (0×0.2) = 4.00 + 0.90 + 0.00 = 4.90"""
        assert score_goal(_goal(8, SmilePhase.INTERVENE, False)) == 4.90


# ── score_goal — urgency_flag behaviour ──────────────────────────────────────

class TestScoreGoalWithUrgency:
    """Tests that isolate the urgency_flag contribution.

    These tests answer: "does urgency_flag actually move the score?"
    """

    def test_urgency_adds_exactly_0_2(self) -> None:
        """Flipping urgency_flag True must add exactly 0.20 to any goal.

        This is the URGENCY_WEIGHT constant. If this test fails, the formula
        is not applying the weight correctly.
        """
        for phase in SmilePhase:
            for p in (1, 5, 10):
                without = score_goal(_goal(p, phase, False))
                with_u = score_goal(_goal(p, phase, True))
                diff = round(with_u - without, 2)
                assert diff == 0.20, (
                    f"p={p}, {phase}: expected urgency diff=0.20, got {diff}"
                )

    def test_urgent_goal_always_scores_higher_than_nonurgent(self) -> None:
        """For any goal, the urgent version must outrank the non-urgent version."""
        for phase in SmilePhase:
            for p in range(1, 11):
                g_normal = _goal(p, phase, False)
                g_urgent = _goal(p, phase, True)
                assert score_goal(g_urgent) > score_goal(g_normal)

    def test_urgency_can_change_rank_between_peers(self) -> None:
        """A lower-phase urgent goal can outrank a higher-phase non-urgent peer
        if the phase difference is only one step (0.30 vs 0.20).

        p=5, SENSE, urgent=True:   (2.50+0.30+0.20) = 3.00
        p=5, MODEL, urgent=False:  (2.50+0.60+0.00) = 3.10
        MODEL still wins here (0.30 gap > 0.20 urgency boost).
        But two phase steps apart (0.60 gap > 0.20) — urgency can't bridge it.
        """
        # SENSE urgent vs MODEL non-urgent: MODEL still wins (0.10 gap)
        sense_urgent = score_goal(_goal(5, SmilePhase.SENSE, True))   # 3.00
        model_normal = score_goal(_goal(5, SmilePhase.MODEL, False))  # 3.10
        assert model_normal > sense_urgent  # phase advantage > urgency boost

        # But urgency can narrow the gap significantly
        gap = round(model_normal - sense_urgent, 2)
        assert gap == pytest.approx(0.10)  # was 0.30 without urgency flag

    def test_urgency_flag_false_by_default(self) -> None:
        """Goal created without urgency_flag must default to False."""
        g = _goal(5, SmilePhase.SENSE)  # no urgent= argument
        assert g.urgency_flag is False
        # Score must equal the non-urgent formula value
        assert score_goal(g) == 2.80


# ── score_goal — general properties ──────────────────────────────────────────

class TestScoreGoalProperties:
    def test_returns_float(self) -> None:
        assert isinstance(score_goal(_goal(5, SmilePhase.SENSE)), float)

    def test_all_phases_produce_valid_scores(self) -> None:
        for phase in SmilePhase:
            for urgent in (True, False):
                s = score_goal(_goal(5, phase, urgent))
                assert isinstance(s, float), f"{phase} urgent={urgent}: not float"

    def test_higher_priority_always_gives_higher_score(self) -> None:
        """For any phase and urgency, priority 10 must beat priority 1."""
        for phase in SmilePhase:
            for urgent in (True, False):
                low = score_goal(_goal(1, phase, urgent))
                high = score_goal(_goal(10, phase, urgent))
                assert high > low, f"{phase} urgent={urgent}: high prio must win"

    def test_phases_strictly_ordered_by_score(self) -> None:
        """Phase weights 1–5 must produce strictly ascending scores at same priority."""
        phases = [
            SmilePhase.SENSE,
            SmilePhase.MODEL,
            SmilePhase.INTERVENE,
            SmilePhase.LEARN,
            SmilePhase.EVOLVE,
        ]
        scores = [score_goal(_goal(5, ph, False)) for ph in phases]
        for i in range(len(scores) - 1):
            assert scores[i] < scores[i + 1], (
                f"{phases[i]}({scores[i]}) should be < {phases[i+1]}({scores[i+1]})"
            )

    def test_deterministic(self) -> None:
        g = _goal(7, SmilePhase.LEARN, True)
        assert score_goal(g) == score_goal(g)

    def test_result_rounded_to_2dp(self) -> None:
        s = score_goal(_goal(3, SmilePhase.MODEL, True))
        assert s == round(s, 2)


# ── score_explanation ─────────────────────────────────────────────────────────

class TestScoreExplanation:
    def test_returns_non_empty_string(self) -> None:
        assert len(score_explanation(_goal(5, SmilePhase.SENSE))) > 30

    def test_contains_score_value(self) -> None:
        g = _goal(5, SmilePhase.SENSE, False)
        assert str(score_goal(g)) in score_explanation(g)

    def test_contains_phase_name(self) -> None:
        for phase in SmilePhase:
            assert str(phase) in score_explanation(_goal(5, phase))

    def test_contains_priority_value(self) -> None:
        assert "7" in score_explanation(_goal(7, SmilePhase.MODEL))

    def test_contains_urgency_info(self) -> None:
        """Explanation must mention urgency so the reasoning is transparent."""
        explanation = score_explanation(_goal(5, SmilePhase.SENSE, True))
        # Should contain "True" or "urgency" to indicate the flag was considered
        assert "True" in explanation or "urgency" in explanation.lower()


# ── sort_goals_by_score ───────────────────────────────────────────────────────

class TestSortGoalsByScore:
    def test_empty_returns_empty(self) -> None:
        assert sort_goals_by_score([]) == []

    def test_single_item_unchanged(self) -> None:
        g = _goal(5, SmilePhase.SENSE)
        assert sort_goals_by_score([g]) == [g]

    def test_sorted_descending_by_score(self) -> None:
        goals = [
            _goal(1, SmilePhase.SENSE, False, "Low"),
            _goal(10, SmilePhase.EVOLVE, True, "High"),
            _goal(5, SmilePhase.INTERVENE, False, "Mid"),
        ]
        result = sort_goals_by_score(goals)
        scores = [score_goal(g) for g in result]
        assert scores == sorted(scores, reverse=True)

    def test_urgent_goal_surfaces_above_nonurgent_peer(self) -> None:
        """Same priority and phase: urgent must come first."""
        g_urgent = _goal(5, SmilePhase.MODEL, True, "Urgent")
        g_normal = _goal(5, SmilePhase.MODEL, False, "Normal")
        result = sort_goals_by_score([g_normal, g_urgent])
        assert result[0].title == "Urgent"

    def test_highest_score_is_first(self) -> None:
        goals = [
            _goal(1, SmilePhase.SENSE, False, "Worst"),
            _goal(10, SmilePhase.EVOLVE, True, "Best"),
        ]
        result = sort_goals_by_score(goals)
        assert result[0].title == "Best"

    def test_lowest_score_is_last(self) -> None:
        goals = [
            _goal(10, SmilePhase.EVOLVE, True, "Best"),
            _goal(1, SmilePhase.SENSE, False, "Worst"),
        ]
        result = sort_goals_by_score(goals)
        assert result[-1].title == "Worst"

    def test_tiebreak_older_goal_first(self) -> None:
        """Equal scores: created_at ascending (older first)."""
        g_old = _goal(5, SmilePhase.SENSE, False, "Older")
        time.sleep(0.02)
        g_new = _goal(5, SmilePhase.SENSE, False, "Newer")
        result = sort_goals_by_score([g_new, g_old])
        assert result[0].title == "Older"

    def test_does_not_mutate_input(self) -> None:
        goals = [
            _goal(9, SmilePhase.EVOLVE, True, "A"),
            _goal(1, SmilePhase.SENSE, False, "B"),
        ]
        first_before = goals[0].title
        sort_goals_by_score(goals)
        assert goals[0].title == first_before
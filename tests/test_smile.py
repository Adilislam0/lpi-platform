"""Tests for SMILE methodology — core to LPI.

All team members should understand SMILE after completing onboarding challenges.
"""
from lpi.models import SmilePhase
from lpi.smile import get_phase_description, validate_phase_transition


class TestPhaseTransitions:
    def test_forward_step_allowed(self) -> None:
        assert validate_phase_transition(SmilePhase.SENSE, SmilePhase.MODEL) is True
        assert validate_phase_transition(SmilePhase.MODEL, SmilePhase.INTERVENE) is True

    def test_backward_allowed(self) -> None:
        """Learning can cause re-sensing — backward is OK."""
        assert validate_phase_transition(SmilePhase.LEARN, SmilePhase.SENSE) is True

    def test_skip_not_allowed(self) -> None:
        """Can't skip from SENSE to INTERVENE."""
        assert validate_phase_transition(SmilePhase.SENSE, SmilePhase.INTERVENE) is False

    def test_same_phase_not_allowed(self) -> None:
        assert validate_phase_transition(SmilePhase.SENSE, SmilePhase.SENSE) is False


class TestPhaseDescriptions:
    def test_all_phases_have_descriptions(self) -> None:
        for phase in SmilePhase:
            desc = get_phase_description(phase)
            assert len(desc) > 10

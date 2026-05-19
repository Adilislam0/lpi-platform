"""SMILE methodology implementation: Sense, Model, Intervene, Learn, Evolve."""
from lpi.models import SmilePhase

PHASE_ORDER = [SmilePhase.SENSE, SmilePhase.MODEL, SmilePhase.INTERVENE, SmilePhase.LEARN, SmilePhase.EVOLVE]


def validate_phase_transition(current: SmilePhase, target: SmilePhase) -> bool:
    """Validate that a phase transition is allowed.
    Forward transitions are always allowed. Backward transitions are allowed
    (learning can cause re-sensing). Skip transitions are not allowed.
    """
    current_idx = PHASE_ORDER.index(current)
    target_idx = PHASE_ORDER.index(target)
    if target_idx == current_idx + 1:
        return True  # forward step
    if target_idx < current_idx:
        return True  # backward (re-evaluation)
    if target_idx == current_idx:
        return False  # no-op
    return False  # skip not allowed


def get_phase_description(phase: SmilePhase) -> str:
    """Return description of what this SMILE phase means."""
    descriptions = {
        SmilePhase.SENSE: "Gathering data, observing reality, identifying signals",
        SmilePhase.MODEL: "Building understanding, forming hypotheses, mapping relationships",
        SmilePhase.INTERVENE: "Taking action, making changes, testing hypotheses",
        SmilePhase.LEARN: "Evaluating results, extracting lessons, measuring impact",
        SmilePhase.EVOLVE: "Adapting strategy, refining approach, scaling what works",
    }
    return descriptions[phase]

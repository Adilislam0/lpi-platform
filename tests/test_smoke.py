def test_imports() -> None:
    from lpi import main

    assert main.app is not None


def test_health(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_smile_phase_order() -> None:
    from lpi.smile import PHASE_ORDER, SmilePhase

    assert PHASE_ORDER[0] == SmilePhase.SENSE
    assert PHASE_ORDER[-1] == SmilePhase.EVOLVE
    assert len(PHASE_ORDER) == 5

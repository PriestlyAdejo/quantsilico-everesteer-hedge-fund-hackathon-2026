from qs_everesteer.contracts import CandidateStatus, StakeMode


def test_contracts():
    assert CandidateStatus.FRONTIER.value == "FRONTIER"
    assert StakeMode.UNKNOWN.value == "UNKNOWN"

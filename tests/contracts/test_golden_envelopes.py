"""Golden tests for Figma Research Console Pydantic envelope mirrors."""

from __future__ import annotations

import re

from qs_everesteer.api_schemas.envelope import SCHEMA_VERSION, ActionResult
from qs_everesteer.api_schemas.examples import all_example_envelopes, example_action_result
from qs_everesteer.api_schemas.humanize import humanize_decision
from qs_everesteer.api_schemas.pages import RaceDecision

_SNAKE_KEY = re.compile(r"^[a-z]+(?:_[a-z0-9]+)+$")
_CAMEL_TOP_LEVEL = {
    "schemaVersion",
    "generatedAt",
    "refreshMode",
    "staleAfterSeconds",
    "sourceId",
    "eventSnapshotId",
}


def _assert_camel_keys(obj: object, *, path: str = "$") -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            assert isinstance(key, str), f"{path}: non-string key {key!r}"
            if path == "$" or key in _CAMEL_TOP_LEVEL:
                assert key in {
                    "schemaVersion",
                    "kind",
                    "provenance",
                    "generatedAt",
                    "stale",
                    "source",
                    "refreshMode",
                    "staleAfterSeconds",
                    "sourceId",
                    "eventSnapshotId",
                    "data",
                    "ok",
                    "message",
                    "code",
                    "timestamp",
                } or not _SNAKE_KEY.match(key), (
                    f"{path}.{key}: expected camelCase (no snake_case) key"
                )
            assert not _SNAKE_KEY.match(key), (
                f"{path}: snake_case key {key!r} leaked into dumped JSON"
            )
            _assert_camel_keys(value, path=f"{path}.{key}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _assert_camel_keys(item, path=f"{path}[{i}]")


def test_every_example_envelope_schema_version_and_camel_case() -> None:
    envelopes = all_example_envelopes()
    assert len(envelopes) == 16
    kinds = {env.kind for env in envelopes}
    assert kinds == {
        "event_status",
        "overview",
        "event_control",
        "round_room",
        "data_lab",
        "experiments",
        "validation",
        "models",
        "feature_lab",
        "ensembles",
        "leaderboard",
        "submission",
        "staking",
        "compute",
        "repository",
        "documentation",
    }

    for env in envelopes:
        assert env.schema_version == SCHEMA_VERSION == 2
        dumped = env.model_dump(by_alias=True, mode="json")
        assert dumped["schemaVersion"] == 2
        assert "schema_version" not in dumped
        assert "generatedAt" in dumped
        assert "generated_at" not in dumped
        _assert_camel_keys(dumped)


def test_action_result_example() -> None:
    result = example_action_result()
    assert isinstance(result, ActionResult)
    assert result.ok is True
    dumped = result.model_dump(by_alias=True, mode="json")
    assert dumped["ok"] is True
    assert dumped["message"] == "Event refreshed"
    assert dumped["code"] == "OK"
    assert "timestamp" in dumped
    _assert_camel_keys(dumped)


def test_humanize_decision_covers_all_race_decisions() -> None:
    for code in RaceDecision:
        human = humanize_decision(code)
        assert human.code is code
        assert human.label
        assert human.tone

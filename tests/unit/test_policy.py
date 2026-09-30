"""Tests del motor de política."""

from __future__ import annotations

from aimoderator.moderation.policy import PolicyEngine
from aimoderator.schemas.common import Action


def test_below_thresholds_allows() -> None:
    evaluation = PolicyEngine().evaluate({"toxicity": 0.1, "spam": 0.2})
    assert evaluation.action is Action.ALLOW
    assert evaluation.categories == []


def test_hate_triggers_block() -> None:
    evaluation = PolicyEngine().evaluate({"hate": 0.9})
    assert evaluation.action is Action.BLOCK
    assert evaluation.categories == ["hate"]


def test_prompt_injection_triggers_block() -> None:
    evaluation = PolicyEngine().evaluate({"prompt_injection": 0.6})
    assert evaluation.action is Action.BLOCK


def test_most_severe_action_wins() -> None:
    evaluation = PolicyEngine().evaluate({"toxicity": 0.75, "hate": 0.9})
    assert evaluation.action is Action.BLOCK
    assert set(evaluation.categories) == {"toxicity", "hate"}


def test_custom_rules_override_defaults() -> None:
    rules = {"thresholds": {"toxicity": 0.2}, "default_action": "flag"}
    evaluation = PolicyEngine(rules).evaluate({"toxicity": 0.3})
    assert evaluation.action is Action.FLAG
    assert evaluation.categories == ["toxicity"]

"""Tests de los esquemas de perfil."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aimoderator.schemas.common import Action, Category
from aimoderator.schemas.profile import EngineConfig, PolicyRules, ProfileCreate


def test_default_engine_config() -> None:
    config = EngineConfig()
    assert config.primary == "heuristic"
    assert config.use_pi_guard is True
    assert config.fallbacks == []


def test_default_policy_matches_engine_defaults() -> None:
    rules = PolicyRules()
    assert rules.thresholds[Category.PROMPT_INJECTION] == 0.5
    assert rules.actions[Category.HATE] is Action.BLOCK
    assert rules.default_action is Action.ALLOW


def test_profile_create_requires_name() -> None:
    with pytest.raises(ValidationError):
        ProfileCreate(name="")


def test_invalid_action_is_rejected() -> None:
    with pytest.raises(ValidationError):
        PolicyRules.model_validate({"actions": {"toxicity": "explode"}})


def test_engine_config_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        EngineConfig.model_validate({"primary": "heuristic", "nope": 1})

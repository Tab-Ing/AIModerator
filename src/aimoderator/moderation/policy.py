"""Motor de política: convierte scores en una acción de moderación."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aimoderator.schemas.common import Action, Category

_SEVERITY: dict[Action, int] = {
    Action.ALLOW: 0,
    Action.FLAG: 1,
    Action.HIDE: 2,
    Action.BLOCK: 3,
    Action.ESCALATE: 4,
}

DEFAULT_POLICY: dict[str, Any] = {
    "thresholds": {
        Category.TOXICITY.value: 0.7,
        Category.HARASSMENT.value: 0.7,
        Category.HATE.value: 0.7,
        Category.SPAM.value: 0.8,
        Category.PROMPT_INJECTION.value: 0.5,
    },
    "actions": {
        Category.TOXICITY.value: Action.FLAG.value,
        Category.HARASSMENT.value: Action.HIDE.value,
        Category.HATE.value: Action.BLOCK.value,
        Category.SPAM.value: Action.FLAG.value,
        Category.PROMPT_INJECTION.value: Action.BLOCK.value,
    },
    "default_action": Action.ALLOW.value,
}


@dataclass(slots=True)
class PolicyEvaluation:
    """Resultado de aplicar la política a los scores de un motor."""

    action: Action
    categories: list[str] = field(default_factory=list)


class PolicyEngine:
    """Aplica umbrales y acciones configurables por categoría."""

    def __init__(self, rules: dict[str, Any] | None = None) -> None:
        merged: dict[str, Any] = {**DEFAULT_POLICY, **(rules or {})}
        self._thresholds: dict[str, float] = {
            key: float(value) for key, value in dict(merged.get("thresholds", {})).items()
        }
        self._actions: dict[str, Action] = {
            key: Action(value) for key, value in dict(merged.get("actions", {})).items()
        }
        self._default_action = Action(merged.get("default_action", Action.ALLOW.value))

    def threshold_for(self, category: str) -> float:
        return self._thresholds.get(category, 1.0)

    def evaluate(self, scores: dict[str, float]) -> PolicyEvaluation:
        triggered: list[str] = []
        action = self._default_action
        for category, score in scores.items():
            if score >= self.threshold_for(category):
                triggered.append(category)
                candidate = self._actions.get(category, self._default_action)
                if _SEVERITY[candidate] > _SEVERITY[action]:
                    action = candidate
        return PolicyEvaluation(action=action, categories=triggered)

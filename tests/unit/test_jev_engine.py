"""Tests del motor Jev AI con HTTP mockeado."""

from __future__ import annotations

import httpx
import pytest
import respx

from aimoderator.core.errors import EngineError
from aimoderator.engines.base import ClassificationRequest
from aimoderator.engines.jev import JevEngine
from aimoderator.schemas.common import Action, Category


@respx.mock
async def test_parses_scores_and_confidence() -> None:
    route = respx.post("https://jev.test/v1/decide").mock(
        return_value=httpx.Response(
            200,
            json={"toxicity": 0.91, "spam": 0.1, "confidence": 0.87, "action": "block"},
        )
    )
    async with httpx.AsyncClient() as client:
        engine = JevEngine(client=client, base_url="https://jev.test", model="m", api_key="secret")
        result = await engine.classify(
            ClassificationRequest(text="malo", categories=[Category.TOXICITY, Category.SPAM])
        )

    assert route.called
    assert result.scores["toxicity"] == 0.91
    assert result.scores["spam"] == 0.1
    assert result.confidence == 0.87
    assert result.action is Action.BLOCK


@respx.mock
async def test_raises_engine_error_on_failure() -> None:
    respx.post("https://jev.test/v1/decide").mock(return_value=httpx.Response(500))
    async with httpx.AsyncClient() as client:
        engine = JevEngine(client=client, base_url="https://jev.test", model="m", api_key="secret")
        with pytest.raises(EngineError):
            await engine.classify(ClassificationRequest(text="malo"))


@respx.mock
async def test_clamps_out_of_range_scores() -> None:
    respx.post("https://jev.test/v1/decide").mock(
        return_value=httpx.Response(200, json={"toxicity": 1.5})
    )
    async with httpx.AsyncClient() as client:
        engine = JevEngine(client=client, base_url="https://jev.test", model="m", api_key="secret")
        result = await engine.classify(
            ClassificationRequest(text="malo", categories=[Category.TOXICITY])
        )
    assert result.scores["toxicity"] == 1.0

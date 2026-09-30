"""Tests del motor Jev AI (Defapi /api/v1/decisions) con HTTP mockeado."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from aimoderator.core.errors import EngineError
from aimoderator.engines.base import ClassificationRequest
from aimoderator.engines.jev import JevEngine
from aimoderator.schemas.common import Category

_URL = "https://jev.test/api/v1/decisions"


def _engine(client: httpx.AsyncClient) -> JevEngine:
    return JevEngine(
        client=client,
        base_url="https://jev.test",
        model="typesafe/jev-1.13",
        api_key="secret",
    )


@respx.mock
async def test_parses_noul_scores_and_severity_confidence() -> None:
    route = respx.post(_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "model": "jev-1.13.0",
                "answers": {
                    "toxicity": {"type": "noul", "noul": 0.91},
                    "spam": {"type": "noul", "noul": 0.1},
                    "severity": {
                        "type": "score",
                        "score": 1.44,
                        "confidence": 0.87,
                        "probabilities": {"0": 0.0, "1": 0.56, "2": 0.44},
                    },
                },
                "usage": {"input_tokens": 10, "output_tokens": 5},
            },
        )
    )
    async with httpx.AsyncClient() as client:
        result = await _engine(client).classify(
            ClassificationRequest(text="malo", categories=[Category.TOXICITY, Category.SPAM])
        )

    assert route.called
    assert result.scores["toxicity"] == 0.91
    assert result.scores["spam"] == 0.1
    assert result.confidence == 0.87
    assert result.raw["usage"]["input_tokens"] == 10


@respx.mock
async def test_sends_state_and_typed_questions() -> None:
    route = respx.post(_URL).mock(
        return_value=httpx.Response(
            200, json={"answers": {"toxicity": {"type": "noul", "noul": 0.0}}}
        )
    )
    async with httpx.AsyncClient() as client:
        await _engine(client).classify(ClassificationRequest(text="hola mundo"))

    request = route.calls.last.request
    body = json.loads(request.content)
    assert body["model"] == "typesafe/jev-1.13"
    assert body["state"] == "hola mundo"
    assert body["questions"]["toxicity"]["type"] == "noul"
    assert body["questions"]["severity"]["type"] == "score"
    assert body["questions"]["severity"]["criteria"]
    assert request.headers["authorization"] == "Bearer secret"


@respx.mock
async def test_raises_engine_error_on_failure() -> None:
    respx.post(_URL).mock(return_value=httpx.Response(500))
    async with httpx.AsyncClient() as client:
        with pytest.raises(EngineError):
            await _engine(client).classify(ClassificationRequest(text="malo"))


@respx.mock
async def test_raises_engine_error_without_answers() -> None:
    respx.post(_URL).mock(return_value=httpx.Response(200, json={"model": "jev-1.13.0"}))
    async with httpx.AsyncClient() as client:
        with pytest.raises(EngineError):
            await _engine(client).classify(ClassificationRequest(text="malo"))


@respx.mock
async def test_clamps_out_of_range_noul() -> None:
    respx.post(_URL).mock(
        return_value=httpx.Response(
            200, json={"answers": {"toxicity": {"type": "noul", "noul": 1.5}}}
        )
    )
    async with httpx.AsyncClient() as client:
        result = await _engine(client).classify(
            ClassificationRequest(text="malo", categories=[Category.TOXICITY])
        )
    assert result.scores["toxicity"] == 1.0

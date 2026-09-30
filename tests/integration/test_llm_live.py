"""Test en vivo del motor LLM (se salta si no hay API key)."""

from __future__ import annotations

import asyncio

import httpx
import pytest

from aimoderator.config import get_settings
from aimoderator.engines.base import ClassificationRequest
from aimoderator.engines.llm import LLMEngine

pytestmark = pytest.mark.live


def test_llm_live_detects_toxicity() -> None:
    settings = get_settings()
    if not settings.llm_api_key:
        pytest.skip("sin AIMODERATOR_LLM_API_KEY")

    async def _run() -> dict[str, float]:
        async with httpx.AsyncClient() as client:
            engine = LLMEngine(
                client=client,
                base_url=settings.llm_base_url,
                model=settings.llm_model,
                api_key=settings.llm_api_key,
                chat_path=settings.llm_chat_path,
            )
            result = await engine.classify(
                ClassificationRequest(text="Sos un idiota, nadie te soporta.")
            )
        return result.scores

    scores = asyncio.run(_run())
    assert scores.get("toxicity", 0.0) > 0.5

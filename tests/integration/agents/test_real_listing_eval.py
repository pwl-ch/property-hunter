"""Integration evaluations for live LLM agents on real listing data."""

import json
import os
from pathlib import Path

import pytest

from property_hunter.adapters.agents import (
    PydanticAIExtractionAgent,
    PydanticAIRegulatoryAgent,
)
from property_hunter.domain.models import CapturedListing
from property_hunter.settings import Settings

FIXTURE_PATH = (
    Path(__file__).parents[2] / "fixtures" / "listings" / "otodom_pepowo_mpzp.json"
)
RUN_LLM_EVALS = os.getenv("PROPERTY_HUNTER_RUN_LLM_EVALS") == "1"


@pytest.mark.llm_eval
@pytest.mark.slow
@pytest.mark.skipif(not RUN_LLM_EVALS, reason="live LLM evaluations are opt-in")
def test_lm_studio_agents_extract_real_otodom_pepowo_listing() -> None:
    """Assess live LM Studio agents on a real Otodom listing snapshot."""
    # given
    listing = _load_fixture_listing(FIXTURE_PATH)
    settings = Settings(
        agent_mode="llm",
        llm_provider="lm_studio",
        lm_studio_base_url="http://127.0.0.1:1234/v1",
        model_name="google/gemma-4-e4b",
    )
    extraction_agent = PydanticAIExtractionAgent(settings=settings)
    regulatory_agent = PydanticAIRegulatoryAgent(settings=settings)

    # when
    extracted = extraction_agent.extract(listing)
    regulatory_summary = regulatory_agent.summarize(listing)

    # then
    assert extracted.price is not None
    assert abs(extracted.price - 319000) <= 1
    assert extracted.area_sqm is not None
    assert abs(extracted.area_sqm - 1173) <= 1
    assert extracted.price_per_sqm is None or abs(extracted.price_per_sqm - 272) <= 2
    assert extracted.city is None or "pępow" in extracted.city.lower()
    assert regulatory_summary.summary
    assert "mpzp" in regulatory_summary.summary.lower() or (
        regulatory_summary.mpzp_status is not None
        and "mention" in regulatory_summary.mpzp_status.lower()
    )


def _load_fixture_listing(path: Path) -> CapturedListing:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return CapturedListing.model_validate(
        {
            "source_site": payload["source_site"],
            "url": payload["source_url"],
            "title": payload["title"],
            "raw_text": payload["raw_text"],
        }
    )

"""Unit tests for listing agent adapters."""

from dataclasses import dataclass

from property_hunter.adapters.agents import (
    PydanticAIExtractionAgent,
    PydanticAIRegulatoryAgent,
    create_listing_agents,
)
from property_hunter.domain.models import (
    CapturedListing,
    ExtractedProperty,
    RegulatorySummary,
)
from property_hunter.settings import Settings


@dataclass
class FakeRunResult[OutputT]:
    """Fake Pydantic AI run result."""

    output: OutputT


class FakeStructuredAgent[OutputT]:
    """Fake Pydantic AI agent that records prompts."""

    def __init__(self, output: OutputT) -> None:
        """Create a fake structured agent."""
        self.output = output
        self.prompts: list[str] = []

    def run_sync(self, user_prompt: str) -> FakeRunResult[OutputT]:
        """Record the prompt and return the configured output."""
        self.prompts.append(user_prompt)
        return FakeRunResult(self.output)


def test_pydantic_ai_extraction_agent_returns_structured_output(
    captured_listing: CapturedListing,
) -> None:
    """Return extracted property output from a Pydantic AI run."""
    # given
    output = ExtractedProperty(
        price=250000,
        area_sqm=1000,
        parcel_id="141201_1.0001.12/3",
        city="Warszawa",
    )
    fake_agent = FakeStructuredAgent(output)
    adapter = PydanticAIExtractionAgent(agent=fake_agent)

    # when
    result = adapter.extract(captured_listing)

    # then
    assert result == output
    assert "Dzialka 1000 m2" in fake_agent.prompts[0]
    assert "otodom.pl" in fake_agent.prompts[0]


def test_pydantic_ai_regulatory_agent_returns_structured_output(
    captured_listing: CapturedListing,
) -> None:
    """Return regulatory summary output from a Pydantic AI run."""
    # given
    output = RegulatorySummary(
        summary="MPZP dopuszcza zabudowe.",
        mpzp_status="mentioned",
        risks=[],
    )
    fake_agent = FakeStructuredAgent(output)
    adapter = PydanticAIRegulatoryAgent(agent=fake_agent)

    # when
    result = adapter.summarize(captured_listing)

    # then
    assert result == output
    assert "MPZP dopuszcza zabudowe" in fake_agent.prompts[0]


def test_create_listing_agents_can_select_heuristic_mode() -> None:
    """Create deterministic agents when heuristic mode is configured."""
    # given
    settings = Settings(agent_mode="heuristic")

    # when
    extraction_agent, regulatory_agent = create_listing_agents(settings)

    # then
    assert extraction_agent.__class__.__name__ == "HeuristicExtractionAgent"
    assert regulatory_agent.__class__.__name__ == "HeuristicRegulatoryAgent"

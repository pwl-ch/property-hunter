"""Agent adapters for extraction and regulatory summaries."""

import logging
import re
from typing import Protocol

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from property_hunter.application.ports import ExtractionAgent, RegulatoryAgent
from property_hunter.domain.models import (
    CapturedListing,
    ExtractedProperty,
    RegulatorySummary,
)
from property_hunter.settings import Settings

logger = logging.getLogger(__name__)


class _AgentRunResult[OutputT](Protocol):
    output: OutputT


class _StructuredAgent[OutputT](Protocol):
    def run_sync(self, user_prompt: str) -> _AgentRunResult[OutputT]:
        """Run the agent synchronously and return structured output."""


class HeuristicExtractionAgent:
    """Local fallback extractor used when no LLM server is configured."""

    def extract(self, listing: CapturedListing) -> ExtractedProperty:
        """Extract common Polish real-estate facts using deterministic rules."""
        logger.info("Running heuristic extraction for %s", listing.source_site)
        text = f"{listing.title}\n{listing.raw_text}"
        price = _first_number(text, r"([\d\s]+(?:[,.]\d+)?)\s*(?:zł|pln)")
        area = _first_number(text, r"([\d\s]+(?:[,.]\d+)?)\s*m(?:2|²|kw)")
        price_per_sqm = None
        if price is not None and area:
            price_per_sqm = round(price / area, 2)
        parcel_id = _first_match(
            text,
            r"\b\d{6}_\d\.\d{4}\.[A-Za-z0-9/.-]+\b",
        )
        city = _first_match(
            text,
            r"(?:miejscowość|miasto|city)[:\s]+([A-ZŁŚŻŹĆŃÓ][\wąćęłńóśźż -]+)",
        )
        street = _first_match(text, r"(?:ul\.|ulica|street)[:\s]+([\wąćęłńóśźż .-]+)")
        return ExtractedProperty(
            price=price,
            price_per_sqm=price_per_sqm,
            area_sqm=area,
            parcel_id=parcel_id,
            city=city,
            street=street,
            regulatory_text_summary=_regulatory_sentence(text),
        )


class HeuristicRegulatoryAgent:
    """Local fallback regulatory summarizer."""

    def summarize(self, listing: CapturedListing) -> RegulatorySummary:
        """Summarize zoning phrases found in the listing text."""
        logger.info("Running heuristic regulatory summary for %s", listing.source_site)
        text = listing.raw_text
        summary = _regulatory_sentence(text) or "No regulatory information detected."
        risks = []
        lowered = text.lower()
        for keyword in ("zalew", "osuwisk", "służebność", "brak mpzp"):
            if keyword in lowered:
                risks.append(keyword)
        mpzp_status = None
        if "mpzp" in lowered:
            mpzp_status = "mentioned"
        elif "wz" in lowered or "warunki zabudowy" in lowered:
            mpzp_status = "wz mentioned"
        return RegulatorySummary(summary=summary, mpzp_status=mpzp_status, risks=risks)


class PydanticAIExtractionAgent:
    """Pydantic AI adapter for structured property extraction."""

    def __init__(
        self,
        agent: _StructuredAgent[ExtractedProperty] | None = None,
        settings: Settings | None = None,
    ) -> None:
        """Create an extraction agent.

        Parameters
        ----------
        agent:
            Optional injected Pydantic AI-compatible agent, mainly for tests.
        settings:
            Runtime settings used when constructing the default LM Studio agent.
        """
        self.agent = agent or _build_agent(
            settings or Settings(),
            output_type=ExtractedProperty,
            instructions=(
                "Extract structured real-estate facts from Polish listing text. "
                "Return only facts supported by the input. Use null when unknown. "
                "Use PLN for price fields and square meters for area_sqm."
            ),
        )

    def extract(self, listing: CapturedListing) -> ExtractedProperty:
        """Extract listing facts through Pydantic AI structured output."""
        logger.info("Running Pydantic AI extraction for %s", listing.source_site)
        result = self.agent.run_sync(_listing_prompt(listing))
        return result.output


class PydanticAIRegulatoryAgent:
    """Pydantic AI adapter for structured regulatory summaries."""

    def __init__(
        self,
        agent: _StructuredAgent[RegulatorySummary] | None = None,
        settings: Settings | None = None,
    ) -> None:
        """Create a regulatory summary agent.

        Parameters
        ----------
        agent:
            Optional injected Pydantic AI-compatible agent, mainly for tests.
        settings:
            Runtime settings used when constructing the default LM Studio agent.
        """
        self.agent = agent or _build_agent(
            settings or Settings(),
            output_type=RegulatorySummary,
            instructions=(
                "Summarize planning, zoning, building-conditions, utility, access, "
                "flood, easement, and legal-risk statements from Polish listing "
                "text. Keep the summary concise and list risks explicitly."
            ),
        )

    def summarize(self, listing: CapturedListing) -> RegulatorySummary:
        """Summarize regulatory listing text through Pydantic AI."""
        logger.info(
            "Running Pydantic AI regulatory summary for %s",
            listing.source_site,
        )
        result = self.agent.run_sync(_listing_prompt(listing))
        return result.output


def create_listing_agents(
    settings: Settings,
) -> tuple[ExtractionAgent, RegulatoryAgent]:
    """Create extraction and regulatory agents from runtime settings.

    Parameters
    ----------
    settings:
        Runtime settings that select the agent mode and model provider.

    Returns
    -------
    tuple[ExtractionAgent, RegulatoryAgent]
        Agent pair used by the analyze-listing use case.
    """
    if settings.agent_mode == "heuristic":
        logger.info("Creating heuristic listing agents")
        return HeuristicExtractionAgent(), HeuristicRegulatoryAgent()
    logger.info(
        "Creating LLM listing agents provider=%s model=%s",
        settings.llm_provider,
        settings.model_name,
    )
    return (
        PydanticAIExtractionAgent(settings=settings),
        PydanticAIRegulatoryAgent(settings=settings),
    )


def _build_agent[OutputT](
    settings: Settings,
    *,
    output_type: type[OutputT],
    instructions: str,
) -> _StructuredAgent[OutputT]:
    base_url = _base_url_for_provider(settings)
    provider = OpenAIProvider(base_url=base_url, api_key=settings.llm_api_key)
    model = OpenAIChatModel(settings.model_name, provider=provider)
    return Agent(model, output_type=output_type, instructions=instructions)


def _base_url_for_provider(settings: Settings) -> str:
    match settings.llm_provider:
        case "lm_studio":
            return settings.lm_studio_base_url
        case "ollama":
            return settings.ollama_base_url


def _listing_prompt(listing: CapturedListing) -> str:
    return (
        f"Source site: {listing.source_site}\n"
        f"URL: {listing.url}\n"
        f"Title: {listing.title}\n\n"
        f"Listing text:\n{listing.raw_text}"
    )


def _first_number(text: str, pattern: str) -> float | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if match is None:
        return None
    value = match.group(1).replace(" ", "").replace(",", ".")
    try:
        return float(value)
    except ValueError:
        return None


def _first_match(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if match is None:
        return None
    return match.group(1).strip(" ,.;")


def _regulatory_sentence(text: str) -> str | None:
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        lowered = sentence.lower()
        if any(word in lowered for word in ("mpzp", "wz", "warunki zabudowy", "zabud")):
            return sentence.strip()
    return None

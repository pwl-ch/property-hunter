"""Agent adapters for extraction and regulatory summaries."""

import re

from property_hunter.domain.models import (
    CapturedListing,
    ExtractedProperty,
    RegulatorySummary,
)


class HeuristicExtractionAgent:
    """Local fallback extractor used when no LLM server is configured."""

    def extract(self, listing: CapturedListing) -> ExtractedProperty:
        """Extract common Polish real-estate facts using deterministic rules."""
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

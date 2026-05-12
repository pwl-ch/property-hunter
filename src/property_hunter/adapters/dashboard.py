"""Streamlit dashboard adapter."""

import logging
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

import httpx
import streamlit as st

from property_hunter.adapters.agents import create_listing_agents
from property_hunter.adapters.sqlite import SQLitePropertyRepository
from property_hunter.domain.models import CapturedListing
from property_hunter.logging import configure_logging
from property_hunter.settings import Settings, get_settings

logger = logging.getLogger(__name__)


def run() -> None:
    """Render the local Streamlit dashboard."""
    settings = get_settings()
    configure_logging(settings.log_level)
    repository = SQLitePropertyRepository(Path(settings.db_path))
    properties = repository.list(limit=500)

    st.set_page_config(page_title="PropertyHunter", layout="wide")
    st.title("PropertyHunter")
    _render_agent_test(settings)

    st.header("Saved properties")
    st.dataframe(
        [
            {
                "title": item.listing.title,
                "price": item.extracted.price,
                "area_sqm": item.extracted.area_sqm,
                "parcel_id": item.extracted.parcel_id,
                "sync": item.sync_status.value,
            }
            for item in properties
        ],
        use_container_width=True,
    )

    if not properties:
        st.info("No analyzed properties saved yet.")
        return

    selected_id = st.selectbox("Property", [item.id for item in properties])
    selected = next((item for item in properties if item.id == selected_id), None)
    if selected is None:
        return
    st.subheader(selected.listing.title)
    st.write(str(selected.listing.url))
    st.json(selected.model_dump(mode="json"))


def _render_agent_test(settings: Settings) -> None:
    st.header("Agent test")
    with st.form("agent-test"):
        input_mode = st.radio(
            "Input",
            ["URL", "Text"],
            horizontal=True,
        )
        url = st.text_input("Listing URL", disabled=input_mode != "URL")
        title = st.text_input("Title", disabled=input_mode != "Text")
        raw_text = st.text_area(
            "Listing content",
            height=220,
            disabled=input_mode != "Text",
        )
        submitted = st.form_submit_button("Run agents")

    if not submitted:
        return

    try:
        if input_mode == "URL":
            listing = _capture_listing_from_url(url, settings.request_timeout_seconds)
        else:
            listing = _capture_listing_from_text(title=title, raw_text=raw_text)
        extraction_agent, regulatory_agent = create_listing_agents(settings)
        extracted = extraction_agent.extract(listing)
        regulatory_summary = regulatory_agent.summarize(listing)
    except Exception as exc:
        logger.exception("Dashboard agent test failed")
        st.error(f"Agent test failed: {exc}")
        return

    st.caption(
        f"{settings.agent_mode} / {settings.llm_provider} / {settings.model_name}"
    )
    st.subheader("Captured listing")
    st.json(listing.model_dump(mode="json"))
    st.subheader("Extracted property")
    st.json(extracted.model_dump(mode="json"))
    st.subheader("Regulatory summary")
    st.json(regulatory_summary.model_dump(mode="json"))


def _capture_listing_from_url(url: str, timeout_seconds: float) -> CapturedListing:
    normalized_url = url.strip()
    if not normalized_url:
        msg = "Listing URL is required."
        raise ValueError(msg)

    logger.info("Fetching listing URL for dashboard agent test")
    response = httpx.get(
        normalized_url,
        headers={"User-Agent": "PropertyHunter/0.1.0"},
        follow_redirects=True,
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    html = response.text
    title = _extract_title(html) or normalized_url
    return CapturedListing.model_validate(
        {
            "source_site": urlparse(str(response.url)).hostname or "unknown",
            "url": str(response.url),
            "title": title,
            "raw_text": _html_to_text(html),
            "raw_html": html,
        }
    )


def _capture_listing_from_text(*, title: str, raw_text: str) -> CapturedListing:
    clean_text = raw_text.strip()
    if not clean_text:
        msg = "Listing content is required."
        raise ValueError(msg)
    return CapturedListing.model_validate(
        {
            "source_site": "manual",
            "url": "https://property-hunter.local/manual-listing",
            "title": title.strip() or "Manual listing",
            "raw_text": clean_text,
        }
    )


def _extract_title(html: str) -> str | None:
    match = re.search(
        r"<title[^>]*>(.*?)</title>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if match is None:
        return None
    return _normalize_whitespace(match.group(1))


def _html_to_text(html: str) -> str:
    parser = _VisibleTextParser()
    parser.feed(html)
    return _normalize_whitespace(" ".join(parser.parts))


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        _ = attrs
        if tag.lower() in {"script", "style", "noscript"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        stripped = data.strip()
        if stripped:
            self.parts.append(stripped)


if __name__ == "__main__":
    run()

"""Unit tests for dashboard helpers."""

import httpx

from property_hunter.adapters.dashboard import (
    _capture_listing_from_text,
    _capture_listing_from_url,
    _extract_title,
    _html_to_text,
)


def test_capture_listing_from_text_builds_manual_listing() -> None:
    """Build a captured listing from pasted text."""
    # given
    title = "Dzialka testowa"
    raw_text = "Cena 100 000 zl. Powierzchnia 1000 m2."

    # when
    listing = _capture_listing_from_text(title=title, raw_text=raw_text)

    # then
    assert listing.source_site == "manual"
    assert listing.title == title
    assert listing.raw_text == raw_text


def test_capture_listing_from_url_fetches_and_normalizes_html(monkeypatch) -> None:
    """Fetch a listing URL and convert the HTML snapshot into text."""
    # given
    html = """
    <html>
      <head><title> Test listing </title><style>.x { color: red; }</style></head>
      <body><h1>Dzialka</h1><script>ignored()</script><p>1000 m2</p></body>
    </html>
    """

    def fake_get(*args, **kwargs) -> httpx.Response:
        _ = args, kwargs
        request = httpx.Request("GET", "https://example.test/listing")
        return httpx.Response(200, request=request, text=html)

    monkeypatch.setattr(httpx, "get", fake_get)

    # when
    listing = _capture_listing_from_url("https://example.test/listing", 5)

    # then
    assert listing.source_site == "example.test"
    assert listing.title == "Test listing"
    assert "Dzialka" in listing.raw_text
    assert "ignored" not in listing.raw_text


def test_html_helpers_extract_visible_text() -> None:
    """Extract title and visible content from an HTML document."""
    # given
    html = "<title> Example\nTitle </title><body>Hello <script>x</script> world</body>"

    # when
    title = _extract_title(html)
    text = _html_to_text(html)

    # then
    assert title == "Example Title"
    assert text == "Example Title Hello world"

"""Unit tests for userscript rendering."""

from property_hunter.adapters.userscript import render_userscript
from property_hunter.settings import Settings


def test_userscript_uses_settings_links() -> None:
    """Render userscript links from settings."""
    # given
    settings = Settings(
        userscript_namespace_url="http://localhost:9999/",
        userscript_analyze_url="http://localhost:9999/custom/analyze",
        userscript_connect_host="localhost",
        userscript_match_patterns=["https://example.test/*"],
    )

    # when
    source = render_userscript(settings)

    # then
    assert "// @namespace    http://localhost:9999/" in source
    assert "// @match        https://example.test/*" in source
    assert "// @connect      localhost" in source
    assert 'url: "http://localhost:9999/custom/analyze"' in source

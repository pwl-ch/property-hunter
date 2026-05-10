"""Userscript payload generation for browser listing capture."""

import json

from property_hunter.settings import Settings


def render_userscript(settings: Settings) -> str:
    """Render the Tampermonkey/Violentmonkey userscript from settings.

    Parameters
    ----------
    settings:
        Runtime settings containing match patterns and local API URLs.

    Returns
    -------
    str
        Browser userscript source code.
    """
    match_lines = "\n".join(
        f"// @match        {pattern}" for pattern in settings.userscript_match_patterns
    )
    analyze_url = json.dumps(settings.userscript_analyze_url)
    return f"""// ==UserScript==
// @name         PropertyHunter Capture
// @namespace    {settings.userscript_namespace_url}
// @version      0.1.0
// @description  Capture property listings for local PropertyHunter analysis.
{match_lines}
// @grant        GM_xmlhttpRequest
// @connect      {settings.userscript_connect_host}
// ==/UserScript==

(function () {{
  "use strict";

  const button = document.createElement("button");
  button.textContent = "Analizuj w PropertyHunter";
  button.style.position = "fixed";
  button.style.right = "16px";
  button.style.bottom = "16px";
  button.style.zIndex = "999999";
  button.style.padding = "10px 14px";
  button.style.border = "0";
  button.style.borderRadius = "6px";
  button.style.background = "#14532d";
  button.style.color = "#ffffff";
  button.style.font = "14px system-ui, sans-serif";
  button.style.cursor = "pointer";

  button.addEventListener("click", () => {{
    const payload = {{
      source_site: window.location.hostname,
      url: window.location.href,
      title: document.title || "Untitled listing",
      raw_text: document.body.innerText || "",
      raw_html: document.documentElement.outerHTML || "",
      captured_at: new Date().toISOString()
    }};

    GM_xmlhttpRequest({{
      method: "POST",
      url: {analyze_url},
      headers: {{ "Content-Type": "application/json" }},
      data: JSON.stringify(payload),
      onload: () => {{
        button.textContent = "Zapisano w PropertyHunter";
        setTimeout(() => {{ button.textContent = "Analizuj w PropertyHunter"; }}, 2400);
      }},
      onerror: () => {{
        button.textContent = "Błąd połączenia";
        setTimeout(() => {{ button.textContent = "Analizuj w PropertyHunter"; }}, 2400);
      }}
    }});
  }});

  document.body.appendChild(button);
}})();
"""

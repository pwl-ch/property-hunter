"""Userscript payload for browser listing capture."""

USERSCRIPT = """// ==UserScript==
// @name         PropertyHunter Capture
// @namespace    http://127.0.0.1:8765/
// @version      0.1.0
// @description  Capture property listings for local PropertyHunter analysis.
// @match        https://*.otodom.pl/*
// @match        https://*.olx.pl/*
// @match        https://*.adresowo.pl/*
// @grant        GM_xmlhttpRequest
// @connect      127.0.0.1
// ==/UserScript==

(function () {
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

  button.addEventListener("click", () => {
    const payload = {
      source_site: window.location.hostname,
      url: window.location.href,
      title: document.title || "Untitled listing",
      raw_text: document.body.innerText || "",
      raw_html: document.documentElement.outerHTML || "",
      captured_at: new Date().toISOString()
    };

    GM_xmlhttpRequest({
      method: "POST",
      url: "http://127.0.0.1:8765/api/analyze",
      headers: { "Content-Type": "application/json" },
      data: JSON.stringify(payload),
      onload: () => {
        button.textContent = "Zapisano w PropertyHunter";
        setTimeout(() => { button.textContent = "Analizuj w PropertyHunter"; }, 2400);
      },
      onerror: () => {
        button.textContent = "Błąd połączenia";
        setTimeout(() => { button.textContent = "Analizuj w PropertyHunter"; }, 2400);
      }
    });
  });

  document.body.appendChild(button);
})();
"""

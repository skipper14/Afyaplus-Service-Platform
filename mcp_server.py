"""MCP server exposing safe clinic discovery tools and a read-only catalog resource."""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer

CLINICS_PATH = Path(__file__).with_name("clinics.json")
server = MCPServer(
    name="afyaplus-clinic-directory",
    version="1.0.0",
    description="Read-only clinic discovery for AfyaPlus agents.",
)

logger = logging.getLogger("afyaplus.mcp")
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False


def _log_call(name: str, outcome: str) -> None:
    """Emit one machine-readable log line for each tool or resource call."""
    logger.info(json.dumps({"event": "mcp_call", "name": name, "outcome": outcome}, separators=(",", ":")))


def _error(code: str, message: str, hint: str, call_name: str) -> dict[str, Any]:
    """Return instructive caller-facing error data without exposing a traceback."""
    _log_call(call_name, code)
    return {"ok": False, "error": {"code": code, "message": message, "hint": hint}}


def _load_clinics() -> list[dict[str, Any]]:
    """Load the local catalog and validate its top-level shape."""
    with CLINICS_PATH.open(encoding="utf-8") as catalog_file:
        clinics = json.load(catalog_file)
    if not isinstance(clinics, list) or not all(isinstance(clinic, dict) for clinic in clinics):
        raise ValueError("clinics.json must contain a list of objects")
    return clinics


@server.tool(name="search_clinics", structured_output=True)
def search_clinics(query: str, country: str | None = None) -> dict[str, Any]:
    """Search clinics by name, city, service, or clinic ID, optionally restricted to an ISO country code."""
    if not isinstance(query, str) or not 2 <= len(query.strip()) <= 80:
        return _error("INVALID_QUERY", "query must contain 2 to 80 characters", "Provide a clinic, city, service, or ID search term.", "search_clinics")
    if country is not None and (not isinstance(country, str) or len(country) != 2 or not country.isupper()):
        return _error("INVALID_COUNTRY", "country must be a two-letter uppercase code", "Use a value such as KE or UG.", "search_clinics")
    try:
        clinics = _load_clinics()
    except (OSError, ValueError, json.JSONDecodeError):
        return _error("CATALOG_UNAVAILABLE", "The clinic catalog could not be read", "Check clinics.json and retry.", "search_clinics")
    needle = query.strip().casefold()
    matches = [
        clinic for clinic in clinics
        if (country is None or clinic.get("country") == country)
        and needle in json.dumps(clinic, separators=(",", ":")).casefold()
    ]
    _log_call("search_clinics", "ok")
    return {"ok": True, "count": len(matches), "clinics": matches}


@server.tool(name="find_available_clinics", structured_output=True)
def find_available_clinics(min_slots: int = 1, country: str | None = None) -> dict[str, Any]:
    """List clinics with at least min_slots available appointment slots, optionally filtered by country."""
    if not isinstance(min_slots, int) or isinstance(min_slots, bool) or not 1 <= min_slots <= 1000:
        return _error("INVALID_MIN_SLOTS", "min_slots must be an integer from 1 to 1000", "Use the minimum number of appointment slots needed.", "find_available_clinics")
    if country is not None and (not isinstance(country, str) or len(country) != 2 or not country.isupper()):
        return _error("INVALID_COUNTRY", "country must be a two-letter uppercase code", "Use a value such as KE or UG.", "find_available_clinics")
    try:
        clinics = _load_clinics()
    except (OSError, ValueError, json.JSONDecodeError):
        return _error("CATALOG_UNAVAILABLE", "The clinic catalog could not be read", "Check clinics.json and retry.", "find_available_clinics")
    matches = [
        clinic for clinic in clinics
        if clinic.get("available_slots", 0) >= min_slots
        and (country is None or clinic.get("country") == country)
    ]
    _log_call("find_available_clinics", "ok")
    return {"ok": True, "count": len(matches), "clinics": matches}


@server.resource("clinics://catalog", name="clinic_catalog", mime_type="application/json")
def clinic_catalog() -> str:
    """Return the complete read-only clinic catalog as JSON for agent grounding."""
    try:
        result = json.dumps({"ok": True, "clinics": _load_clinics()}, separators=(",", ":"))
    except (OSError, ValueError, json.JSONDecodeError):
        _log_call("clinic_catalog", "CATALOG_UNAVAILABLE")
        return json.dumps({"ok": False, "error": {"code": "CATALOG_UNAVAILABLE", "message": "The clinic catalog could not be read", "hint": "Check clinics.json and retry."}})
    _log_call("clinic_catalog", "ok")
    return result


if __name__ == "__main__":
    asyncio.run(server.run_stdio_async())
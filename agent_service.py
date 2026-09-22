"""Deterministic LangChain agent adapter for the AfyaPlus MCP clinic tools."""

import re
from dataclasses import dataclass
from typing import Any

from langchain_core.tools import StructuredTool

from mcp_server import find_available_clinics, search_clinics


@dataclass(frozen=True)
class AgentAnswer:
    """A grounded answer plus the tool trace needed for auditability."""

    answer: str
    tools_called: list[str]
    grounded: bool


def _country_code(question: str) -> str | None:
    """Extract a supported country code or country name from a user question."""
    country_names = {"kenya": "KE", "uganda": "UG"}
    lowered = question.casefold()
    for country_name, country_code in country_names.items():
        if country_name in lowered or re.search(rf"\b{country_code}\b", question):
            return country_code
    return None


def _toolset() -> dict[str, StructuredTool]:
    """Expose the MCP functions through LangChain's tool interface."""
    return {
        "search_clinics": StructuredTool.from_function(
            func=search_clinics,
            name="search_clinics",
            description="Search the MCP clinic catalog by service, city, name, or ID.",
        ),
        "find_available_clinics": StructuredTool.from_function(
            func=find_available_clinics,
            name="find_available_clinics",
            description="Find MCP clinics with available appointment slots.",
        ),
    }


def answer_question(question: str) -> AgentAnswer:
    """Answer a supported multi-step clinic question using two MCP-backed LangChain tools."""
    if not isinstance(question, str) or not 10 <= len(question.strip()) <= 500:
        return AgentAnswer(
            "The clinic data cannot answer this: ask about available clinics and a supported service or country.",
            [],
            False,
        )
    country = _country_code(question)
    service_match = re.search(r"\b(diagnostics|pharmacy|maternal health|general practice)\b", question.casefold())
    if country is None or service_match is None or "available" not in question.casefold():
        return AgentAnswer(
            "The clinic data cannot answer this: it only contains clinic services, locations, and available slot counts.",
            [],
            False,
        )

    tools = _toolset()
    available = tools["find_available_clinics"].invoke({"min_slots": 1, "country": country})
    matching_service = tools["search_clinics"].invoke({"query": service_match.group(1), "country": country})
    if not available.get("ok") or not matching_service.get("ok"):
        return AgentAnswer(
            "The clinic data cannot answer this because one of the MCP lookups failed.",
            ["find_available_clinics", "search_clinics"],
            False,
        )
    available_ids = {clinic["clinic_id"] for clinic in available["clinics"]}
    matches = [clinic for clinic in matching_service["clinics"] if clinic["clinic_id"] in available_ids]
    if not matches:
        return AgentAnswer(
            f"The clinic data cannot answer this with a positive match: no {service_match.group(1)} clinic in {country} has available slots.",
            ["find_available_clinics", "search_clinics"],
            True,
        )
    descriptions = ", ".join(f"{clinic['name']} ({clinic['available_slots']} slots)" for clinic in matches)
    return AgentAnswer(
        f"Available {service_match.group(1)} clinics in {country}: {descriptions}.",
        ["find_available_clinics", "search_clinics"],
        True,
    )
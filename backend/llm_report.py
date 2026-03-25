"""
LangChain + OpenAI structured insights for Reports. No key => skip gracefully.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class GraphNode(BaseModel):
    id: str = Field(..., max_length=80)
    label: str = Field(..., max_length=120)
    type: str = Field(default="entity", max_length=40)


class GraphEdge(BaseModel):
    source: str = Field(..., max_length=80)
    target: str = Field(..., max_length=80)
    relation: str = Field(default="related", max_length=80)


class ReportInsights(BaseModel):
    executive_summary: str = Field(default="", max_length=4000)
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)


def _compact_incidents(incidents: List[Dict[str, Any]], limit: int = 40) -> str:
    lines = []
    for inc in incidents[:limit]:
        lines.append(
            json.dumps(
                {
                    "title": (inc.get("title") or "")[:200],
                    "severity": inc.get("severity"),
                    "points": inc.get("points"),
                    "trustScore": inc.get("trustScore"),
                    "source": inc.get("source"),
                    "timestamp": inc.get("timestamp"),
                    "type": inc.get("type"),
                },
                default=str,
            )
        )
    return "\n".join(lines)


def generate_insights(
    incidents: List[Dict[str, Any]],
    peak_bucket: Optional[Dict[str, Any]] = None,
    tone: str = "neutral",
    length: str = "short",
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Returns (payload_dict, error_message). payload None if skipped or failed.
    """
    api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not api_key:
        return None, None

    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI
    except ImportError as e:
        logger.warning("langchain_openai not available: %s", e)
        return None, "LLM dependencies not installed"

    model_name = (os.environ.get("OPENAI_REPORT_MODEL") or "gpt-4o-mini").strip()

    length_hint = {
        "short": "2–4 sentences",
        "medium": "1 short paragraph (5–7 sentences)",
        "long": "2 short paragraphs",
    }.get(length, "2–4 sentences")

    peak_line = ""
    if peak_bucket and peak_bucket.get("total"):
        peak_line = (
            f"Busiest time bucket in data (for context only): "
            f"{peak_bucket.get('label')} with {peak_bucket.get('total')} incidents in that bucket.\n"
        )

    system = (
        "You analyze public news-style incident signals for a crisis-awareness dashboard. "
        "Do not invent incidents or numbers. Only generalize from the JSON lines given. "
        "Output must match the schema: executive_summary, nodes, edges. "
        "Entity graph: at most 20 nodes and 30 edges; ids must be short alphanumeric slugs; "
        "connect entities (places, agencies, topics) mentioned or implied in the headlines."
    )
    user = (
        f"Tone: {tone}. Summary length: {length_hint}.\n"
        f"{peak_line}"
        "Incident records (JSON lines):\n"
        f"{_compact_incidents(incidents)}\n"
    )

    try:
        llm = ChatOpenAI(
            model=model_name,
            temperature=0.2,
            api_key=api_key,
            max_tokens=1200,
        )
        structured = llm.with_structured_output(ReportInsights)
        out: ReportInsights = structured.invoke(
            [SystemMessage(content=system), HumanMessage(content=user)]
        )
        nodes = [n.model_dump() for n in out.nodes[:20]]
        edges = [e.model_dump() for e in out.edges[:30]]
        return (
            {
                "executive_summary": (out.executive_summary or "")[:4000],
                "entity_graph": {"nodes": nodes, "edges": edges},
            },
            None,
        )
    except Exception as e:
        logger.exception("LLM report failed")
        return None, str(e)[:500]

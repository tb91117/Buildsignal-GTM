"""BuildSignal's building-material opportunity intelligence graph.

The supervisor fans work out to three specialist agents. Their findings are
merged through a reducer, checked by a critic, qualified with deterministic
rules, and converted into a sales brief. External action is always held for
human approval.
"""

from __future__ import annotations

import operator
import time
import uuid
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from ..config import Settings, get_settings
from ..models import (
    AgentFinding,
    OpportunityDecision,
    OpportunityOutcome,
    OpportunityRequest,
    ResearchTask,
    SalesBrief,
)
from ..services.opportunity_intelligence import OpportunityIntelligence, get_intelligence


class OpportunityState(TypedDict, total=False):
    request: OpportunityRequest
    task: ResearchTask
    findings: Annotated[list[AgentFinding], operator.add]
    gaps: list[str]
    critic_passes: int
    decision: OpportunityDecision
    brief: SalesBrief
    routing_status: str
    agent_trace: Annotated[list[str], operator.add]


def _dispatch_research(state: OpportunityState) -> list[Send]:
    request = state["request"]
    tasks = (
        ResearchTask(
            role="account_research",
            objective="Assess the account, buyer role, and commercial fit using supplied evidence.",
        ),
        ResearchTask(
            role="project_signal",
            objective=(
                "Assess project scope, stage, location, value, deadline, and product relevance."
            ),
        ),
        ResearchTask(
            role="intent_attribution",
            objective=(
                "Assess buying intent, urgency, source quality, and recommended response speed."
            ),
        ),
    )
    return [Send("research_worker", {"request": request, "task": task}) for task in tasks]


class OpportunityPipeline:
    """Compiled LangGraph workflow with replaceable intelligence services."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        intelligence: OpportunityIntelligence | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._intelligence = intelligence or get_intelligence(self.settings)
        self._graph = self._build()

    async def _supervisor(self, state: OpportunityState) -> OpportunityState:
        return {"agent_trace": ["supervisor: dispatched 3 specialist agents"]}

    async def _research_worker(self, state: OpportunityState) -> OpportunityState:
        task = state["task"]
        finding = await self._intelligence.research(task, state["request"])
        return {
            "findings": [finding],
            "agent_trace": [f"{task.role}: completed ({finding.confidence:.0%} confidence)"],
        }

    async def _critic(self, state: OpportunityState) -> OpportunityState:
        request = state["request"]
        gaps: list[str] = []
        if not request.project_name:
            gaps.append("project name")
        if not request.product_category:
            gaps.append("product category")
        if request.estimated_value is None:
            gaps.append("estimated opportunity value")
        if not request.deadline:
            gaps.append("decision or bid deadline")
        return {
            "gaps": gaps,
            "critic_passes": state.get("critic_passes", 0) + 1,
            "agent_trace": [
                "evidence_critic: sufficient for scoring"
                if len(gaps) <= 2
                else f"evidence_critic: {len(gaps)} material gaps flagged"
            ],
        }

    async def _gap_fill(self, state: OpportunityState) -> OpportunityState:
        finding = await self._intelligence.fill_gaps(state["request"], state["gaps"])
        return {
            "findings": [finding],
            "agent_trace": ["gap_fill: prepared targeted discovery questions"],
        }

    @staticmethod
    def _after_critic(state: OpportunityState) -> str:
        if len(state.get("gaps", [])) > 2 and state.get("critic_passes", 0) < 2:
            return "gap_fill"
        return "qualify"

    async def _qualify(self, state: OpportunityState) -> OpportunityState:
        decision = self._intelligence.qualify(state["request"], state.get("gaps", []))
        return {
            "decision": decision,
            "agent_trace": [f"opportunity_qualifier: {decision.tier} ({decision.score}/100)"],
        }

    async def _strategize(self, state: OpportunityState) -> OpportunityState:
        brief = await self._intelligence.create_brief(
            state["request"], state["findings"], state["decision"]
        )
        return {"brief": brief, "agent_trace": ["sales_strategist: brief and response drafted"]}

    async def _review_gate(self, state: OpportunityState) -> OpportunityState:
        status = "awaiting_human_approval" if state["decision"].tier != "Pass" else "archived"
        return {
            "routing_status": status,
            "agent_trace": [f"review_gate: {status}"],
        }

    def _build(self) -> object:
        graph = StateGraph(OpportunityState)
        graph.add_node("supervisor", self._supervisor)
        graph.add_node("research_worker", self._research_worker)
        graph.add_node("evidence_critic", self._critic)
        graph.add_node("gap_fill", self._gap_fill)
        graph.add_node("qualify", self._qualify)
        graph.add_node("strategize", self._strategize)
        graph.add_node("review_gate", self._review_gate)

        graph.add_edge(START, "supervisor")
        graph.add_conditional_edges("supervisor", _dispatch_research, ["research_worker"])
        graph.add_edge("research_worker", "evidence_critic")
        graph.add_conditional_edges(
            "evidence_critic",
            self._after_critic,
            {"gap_fill": "gap_fill", "qualify": "qualify"},
        )
        graph.add_edge("gap_fill", "evidence_critic")
        graph.add_edge("qualify", "strategize")
        graph.add_edge("strategize", "review_gate")
        graph.add_edge("review_gate", END)
        return graph.compile()

    async def run(self, request: OpportunityRequest) -> OpportunityOutcome:
        started = time.perf_counter()
        final: OpportunityState = await self._graph.ainvoke(  # type: ignore[attr-defined]
            {"request": request, "findings": [], "agent_trace": [], "critic_passes": 0}
        )
        return OpportunityOutcome(
            opportunity_id=f"opp_{uuid.uuid4().hex[:10]}",
            request=request,
            findings=final["findings"],
            decision=final["decision"],
            brief=final["brief"],
            routing_status=final["routing_status"],
            agent_trace=final["agent_trace"],
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
        )


def build_opportunity_pipeline(
    settings: Settings | None = None,
    *,
    intelligence: OpportunityIntelligence | None = None,
) -> OpportunityPipeline:
    return OpportunityPipeline(settings, intelligence=intelligence)

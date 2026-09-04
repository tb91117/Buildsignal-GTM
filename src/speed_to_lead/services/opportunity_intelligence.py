"""Specialist intelligence services for the BuildSignal opportunity graph."""

from __future__ import annotations

import json
import re
from typing import Protocol

from ..config import Settings
from ..models import (
    AgentFinding,
    OpportunityDecision,
    OpportunityRequest,
    ResearchTask,
    SalesBrief,
)


class OpportunityIntelligence(Protocol):
    async def research(self, task: ResearchTask, request: OpportunityRequest) -> AgentFinding: ...

    async def fill_gaps(self, request: OpportunityRequest, gaps: list[str]) -> AgentFinding: ...

    def qualify(self, request: OpportunityRequest, gaps: list[str]) -> OpportunityDecision: ...

    async def create_brief(
        self,
        request: OpportunityRequest,
        findings: list[AgentFinding],
        decision: OpportunityDecision,
    ) -> SalesBrief: ...


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in terms)


class DemoOpportunityIntelligence:
    """Deterministic, auditable agents used for the keyless demo and tests."""

    async def research(self, task: ResearchTask, request: OpportunityRequest) -> AgentFinding:
        if task.role == "account_research":
            evidence = [f"Company supplied: {request.company}"]
            if request.decision_maker_role:
                evidence.append(f"Buyer role supplied: {request.decision_maker_role}")
            summary = f"{request.company} is a named commercial account with a reachable contact."
        elif task.role == "project_signal":
            evidence = []
            for label, value in (
                ("Project", request.project_name),
                ("Location", request.project_location),
                ("Stage", request.project_stage),
                ("Product", request.product_category),
                ("Deadline", request.deadline),
            ):
                if value:
                    evidence.append(f"{label}: {value}")
            summary = "Project scope is concrete enough to map to a product and sales motion."
        else:
            intent = (
                "high"
                if _contains_any(
                    request.message, ("quote", "pricing", "bid", "spec", "purchase", "need")
                )
                else "exploratory"
            )
            evidence = [f"Source: {request.source}", f"Detected intent: {intent}"]
            summary = (
                f"The inquiry shows {intent} commercial intent and should be triaged promptly."
            )
        confidence = min(0.95, 0.55 + 0.08 * len(evidence))
        return AgentFinding(
            agent=task.role, summary=summary, evidence=evidence, confidence=confidence
        )

    async def fill_gaps(self, request: OpportunityRequest, gaps: list[str]) -> AgentFinding:
        questions = [f"Confirm {gap}." for gap in gaps]
        return AgentFinding(
            agent="gap_fill",
            summary="Missing fields were converted into targeted discovery questions.",
            evidence=questions,
            confidence=0.9,
        )

    def qualify(self, request: OpportunityRequest, gaps: list[str]) -> OpportunityDecision:
        score = 20
        reasons = ["named company and valid business inquiry"]
        domain = str(request.email).rsplit("@", 1)[-1].lower()
        if domain not in {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com"}:
            score += 15
            reasons.append("business email domain")
        if request.project_name:
            score += 15
            reasons.append("named project")
        if request.product_category:
            score += 15
            reasons.append("product category identified")
        if request.estimated_value is not None:
            score += 15
            reasons.append("commercial value supplied")
        if request.deadline:
            score += 10
            reasons.append("decision deadline supplied")
        if _contains_any(request.message, ("quote", "pricing", "bid", "purchase", "need")):
            score += 10
            reasons.append("high-intent language")
        score = min(score, 100)
        tier = "Pursue" if score >= 70 else "Review" if score >= 45 else "Pass"
        return OpportunityDecision(
            score=score, tier=tier, reasons=reasons, missing_information=gaps
        )

    async def create_brief(
        self,
        request: OpportunityRequest,
        findings: list[AgentFinding],
        decision: OpportunityDecision,
    ) -> SalesBrief:
        product = request.product_category or "the requested building-material solution"
        project = request.project_name or "the project"
        first_name = (request.contact_name or "there").split()[0]
        questions = [
            f"What performance and certification requirements apply to {product}?",
            f"Who owns specification approval and purchasing for {project}?",
            "What is the decision timeline and expected order quantity?",
        ]
        questions.extend(f"Can you confirm the {gap}?" for gap in decision.missing_information[:2])
        return SalesBrief(
            executive_summary=(
                f"{request.company} submitted a {decision.tier.lower()} opportunity for {project}; "
                f"the evidence supports a {decision.score}/100 qualification score."
            ),
            recommended_angle=(
                f"Lead with technical fit and response speed for {product}, then validate the "
                "specifier, purchasing path, and project schedule."
            ),
            discovery_questions=questions,
            response_subject=f"Re: {project} — {product}",
            response_body=(
                f"Hi {first_name},\n\nThanks for sharing the details for {project}. We can help "
                f"evaluate the right {product} option and move quickly around your schedule. "
                "I have a few technical and commercial questions so we can recommend the right "
                "path without slowing the project down. Would a 20-minute review this week "
                "work?\n\n"
                "Best,\nBuildSignal Team"
            ),
        )


class OpenAIOpportunityIntelligence(DemoOpportunityIntelligence):
    """Uses the Responses API for specialist synthesis while preserving deterministic scoring."""

    def __init__(self, api_key: str, model: str) -> None:
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def _respond(self, instructions: str, payload: dict[str, object]) -> str:
        response = await self._client.responses.create(
            model=self._model,
            instructions=instructions,
            input=json.dumps(payload, default=str),
            max_output_tokens=1000,
        )
        return response.output_text.strip()

    async def research(self, task: ResearchTask, request: OpportunityRequest) -> AgentFinding:
        baseline = await super().research(task, request)
        summary = await self._respond(
            (
                f"You are the {task.role} specialist in a building-material GTM system. "
                "Use only the supplied fields and baseline evidence. Do not invent facts. "
                "Return a concise evidence-led assessment in plain text."
            ),
            {
                "objective": task.objective,
                "request": request.model_dump(),
                "evidence": baseline.evidence,
            },
        )
        summary = summary or baseline.summary
        return baseline.model_copy(
            update={"summary": summary, "confidence": min(0.95, baseline.confidence + 0.05)}
        )

    async def create_brief(
        self,
        request: OpportunityRequest,
        findings: list[AgentFinding],
        decision: OpportunityDecision,
    ) -> SalesBrief:
        baseline = await super().create_brief(request, findings, decision)
        body = await self._respond(
            (
                "You are a senior building-material sales strategist. Draft a concise first "
                "response under 130 words. Use only supplied facts, acknowledge the project, "
                "ask for a short technical review, and make no unsupported product claims. "
                "Return only the email body."
            ),
            {
                "request": request.model_dump(),
                "decision": decision.model_dump(),
                "findings": [finding.model_dump() for finding in findings],
            },
        )
        body = re.sub(r"^```(?:text)?\s*|\s*```$", "", body).strip()
        body = body or baseline.response_body
        return baseline.model_copy(update={"response_body": body})


def get_intelligence(settings: Settings) -> OpportunityIntelligence:
    if settings.openai_enabled and settings.openai_api_key:
        return OpenAIOpportunityIntelligence(settings.openai_api_key, settings.openai_model)
    return DemoOpportunityIntelligence()

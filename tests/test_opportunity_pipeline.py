"""BuildSignal multi-agent workflow behavior."""

from speed_to_lead.agents import OpportunityPipeline, build_opportunity_pipeline
from speed_to_lead.models import OpportunityRequest
from speed_to_lead.services.opportunity_intelligence import DemoOpportunityIntelligence


def _request(**overrides: object) -> OpportunityRequest:
    values: dict[str, object] = {
        "email": "maria@northstarbuild.com",
        "contact_name": "Maria Chen",
        "company": "Northstar Construction",
        "message": "Need a quote for facade panels on a 240-unit project.",
        "source": "architect referral",
        "product_category": "fiber cement facade panels",
        "project_name": "Riverfront Residences",
        "project_location": "Minneapolis, MN",
        "project_stage": "design development",
        "estimated_value": 425000,
        "deadline": "2026-09-18",
        "decision_maker_role": "Preconstruction Director",
    }
    values.update(overrides)
    return OpportunityRequest.model_validate(values)


def _pipeline() -> OpportunityPipeline:
    return build_opportunity_pipeline(intelligence=DemoOpportunityIntelligence())


async def test_complete_project_is_pursue() -> None:
    result = await _pipeline().run(_request())
    assert result.decision.tier == "Pursue"
    assert result.decision.score >= 70
    assert result.routing_status == "awaiting_human_approval"
    assert result.brief.requires_human_approval


async def test_three_specialists_contribute_findings() -> None:
    result = await _pipeline().run(_request())
    agents = {finding.agent for finding in result.findings}
    assert {"account_research", "project_signal", "intent_attribution"} <= agents
    assert any(step.startswith("supervisor:") for step in result.agent_trace)


async def test_incomplete_request_triggers_gap_fill() -> None:
    result = await _pipeline().run(
        _request(
            email="owner@gmail.com",
            project_name=None,
            product_category=None,
            estimated_value=None,
            deadline=None,
            message="Just exploring options.",
        )
    )
    assert result.decision.tier == "Pass"
    assert "project name" in result.decision.missing_information
    assert any(finding.agent == "gap_fill" for finding in result.findings)
    assert result.routing_status == "archived"


async def test_results_are_auditable() -> None:
    result = await _pipeline().run(_request())
    assert result.decision.reasons
    assert all(finding.evidence for finding in result.findings)
    assert result.agent_trace[-1] == "review_gate: awaiting_human_approval"

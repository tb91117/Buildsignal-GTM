# BuildSignal architecture

## Design goal

BuildSignal converts an inbound building-material opportunity into a decision a salesperson can trust. The workflow separates evidence gathering, scoring, and writing so the model never silently decides the commercial outcome.

## Runtime flow

1. FastAPI validates the inbound payload as `OpportunityRequest`.
2. The supervisor fans out three `ResearchTask` messages with LangGraph `Send`.
3. A shared worker executes each role through the `OpportunityIntelligence` protocol.
4. LangGraph reducers merge `AgentFinding` objects and trace entries safely.
5. The evidence critic identifies missing project name, product category, value, and deadline.
6. When more than two material fields are absent, the gap-fill agent creates targeted questions and returns once through the critic.
7. The qualifier computes a deterministic 0–100 score and assigns Pursue, Review, or Pass.
8. The strategist prepares an executive summary, sales angle, questions, subject, and response body.
9. The review gate archives Pass opportunities and holds all others for a person to approve.

## Agent responsibilities

| Agent | Input | Output | Guardrail |
|---|---|---|---|
| Supervisor | Valid opportunity | Three bounded tasks | Fixed role allow-list |
| Account researcher | Company and contact evidence | Account-fit finding | Supplied facts only |
| Project-signal analyst | Project fields | Scope and timing finding | No external facts invented |
| Intent-attribution analyst | Message and source | Intent finding | Evidence included |
| Evidence critic | Request and findings | Gaps | Maximum two passes |
| Opportunity qualifier | Request and gaps | Score, tier, reasons | Pure deterministic rules |
| Sales strategist | Findings and decision | Sales brief and response | No unsupported product claims |
| Review gate | Decision | Approval state | Never auto-sends |

## State and reducers

`OpportunityState` is a typed shared state. `findings` and `agent_trace` use additive reducers because the specialist workers run in parallel. The other fields are written by one owning node. This prevents last-writer-wins data loss during fan-out/fan-in.

The final `OpportunityOutcome` is intentionally verbose: it is both the API response and an audit record. A reviewer can reconstruct which agents ran, what they saw, why the score was assigned, and what action is proposed.

## Scoring

The baseline starts at 20 for a named company and valid inquiry. It adds:

| Signal | Points |
|---|---:|
| Business email domain | 15 |
| Named project | 15 |
| Product category | 15 |
| Estimated commercial value | 15 |
| Decision or bid deadline | 10 |
| High-intent language | 10 |

Scores of 70 or more are `Pursue`, 45–69 are `Review`, and lower scores are `Pass`. This simple policy is a starting hypothesis, not a trained prediction. In a pilot, thresholds and weights should be calibrated against won/lost CRM outcomes.

## Deterministic and live implementations

`DemoOpportunityIntelligence` produces deterministic findings and briefs. It keeps the demo reliable, makes tests fast, and provides a fallback when network or quota is unavailable.

`OpenAIOpportunityIntelligence` subclasses the demo implementation. It uses the OpenAI Responses API for evidence-constrained specialist synthesis and email writing while retaining deterministic scoring. Selection occurs only when `DEMO_MODE=false` and `OPENAI_API_KEY` is present.

## Production extension points

- Replace supplied evidence with permissioned CRM, project-feed, specification, or bid-portal connectors.
- Persist checkpoints and opportunities in Postgres; move background jobs to Redis.
- Attach source URLs and timestamps to every evidence item.
- Add identity, tenant isolation, prompt-injection screening, and PII retention policy.
- Connect the review gate to CRM task creation, not direct autonomous sending.
- Track precision at Pursue, rep acceptance, meeting conversion, and time-to-first-action.

## Code-review route

Start at `api/main.py` for the HTTP boundary, then read `models.py`, `agents/opportunity_graph.py`, and `services/opportunity_intelligence.py`. Finish with `tests/test_opportunity_pipeline.py`; the tests capture the intended commercial behavior better than the implementation details.

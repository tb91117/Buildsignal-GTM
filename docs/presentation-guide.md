# BuildSignal presentation guide

## One-sentence pitch

BuildSignal is a human-governed multi-agent system that turns incomplete building-material inquiries into auditable project priorities and ready-to-review sales responses.

## Why it fits Monarch

Lead with the business pattern, not a claim about Monarch's internal systems: technical product sales depend on identifying a real project, understanding who influences the specification and purchase, responding before the bid window closes, and keeping the rep accountable for the final action. BuildSignal demonstrates how an AI workflow can compress that research and preparation cycle without hiding its reasoning.

## Five-slide story

1. **Problem:** opportunity signals are fragmented, uneven, and time-sensitive.
2. **Product:** three specialists research account, project, and intent in parallel.
3. **Trust:** evidence critic, deterministic scoring, complete trace, and human approval.
4. **Demo:** compare a complete facade opportunity with an incomplete renovation inquiry.
5. **Pilot:** connect one approved source and CRM, then measure response time and rep acceptance.

## Three-minute live demo

1. Open the dashboard and say: “This is a project-opportunity workbench, not a generic chatbot.”
2. Submit the preloaded Riverfront Medical Center example.
3. Point to the three specialist cards and explain that LangGraph dispatches them concurrently.
4. Show the score reasons. Emphasize that the model writes summaries but does not assign hidden points.
5. Show the response draft and `awaiting_human_approval` status.
6. Remove project, product, value, and deadline, then submit again.
7. Show the gap-fill trace and discovery questions; explain that the system does not manufacture missing facts.
8. Close with: “A pilot would replace typed inputs with one permissioned opportunity source and write an approval task back to the CRM.”

Keep `DEMO_MODE=true` as the presentation fallback. It exercises the same graph without depending on Wi-Fi or API availability. Use live mode only as an optional second pass.

## Code walkthrough

- `models.py`: contracts that make every graph handoff explicit.
- `opportunity_graph.py`: supervisor fan-out, reducers, critic loop, qualification, strategy, review gate.
- `opportunity_intelligence.py`: protocol plus deterministic and OpenAI implementations.
- `api/main.py`: lifecycle and `/opportunities/sync` boundary.
- `demo_ui.py`: a thin UI that renders the structured result.
- `test_opportunity_pipeline.py`: proof of branch behavior, parallel roles, and audit trail.

## Interview questions and strong answers

**Why multi-agent instead of one prompt?** The tasks have different evidence criteria, can run concurrently, and can be inspected independently. A single prompt would be cheaper for very low volume, so the architecture should earn its complexity through reusable tools and traceability.

**Is the model really deciding which opportunities to pursue?** No. The model synthesizes evidence and drafts language. A deterministic policy assigns the demo score, and a person approves action. This makes the prototype safer and easier to calibrate.

**How do you prevent hallucinations?** Prompts limit synthesis to supplied fields, findings carry explicit evidence, missing data becomes questions, and no autonomous send occurs. Production also needs source citations, content filtering, evals, and monitoring.

**Why LangGraph?** The workflow needs typed shared state, parallel specialist dispatch, reducer-based fan-in, conditional gap handling, and a durable path toward checkpoints and human interruption.

**What would you build next?** One real, approved signal connector; persistent state; CRM review tasks; a labeled historical evaluation set; and a dashboard for precision, acceptance rate, latency, and conversion.

**What is intentionally mocked?** External project research, CRM persistence, and message sending. The graph orchestration, scoring logic, API contract, review state, and OpenAI synthesis path are implemented.

**How would you evaluate it?** Offline: field extraction accuracy, citation correctness, tier precision/recall, draft rubric scores, latency, and cost. Online: Pursue precision, rep acceptance, time to first action, meetings, and pipeline influenced, compared with the current process.

## Demo recovery

- If the API key or network fails, set `DEMO_MODE=true` and restart.
- If the browser is unavailable, run `uv run speed-to-lead opportunity-demo`.
- If asked about a surprising score, read the `reasons` array and calculate the points aloud.
- Never imply the demo has live Monarch data or production integrations.

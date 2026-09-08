"""FastAPI app: fast webhook intake + async processing, plus a sync endpoint.

POST /leads        → verify, normalize, enqueue, 202 (the real path)
POST /leads/sync   → run the pipeline inline and return the full outcome
GET  /health       → liveness
GET  /metrics      → funnel snapshot (JSON)   ·   /metrics/prometheus (text)
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import FastAPI, Header, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from ..agents import build_opportunity_pipeline, build_pipeline
from ..analytics import get_metrics
from ..config import get_settings
from ..logging import configure_logging, get_logger
from ..models import InboundLead, LeadOutcome, OpportunityOutcome, OpportunityRequest
from ..normalize import normalize_lead
from ..observability import setup_tracing
from ..worker import InMemoryQueue
from .demo_ui import build_demo_html
from .security import verify_signature

log = get_logger(__name__)

_FRONTEND_DIST = Path(__file__).resolve().parents[3] / "frontend" / "dist"


async def _consume(app: FastAPI) -> None:
    """Background worker: drain the queue and run each lead through the graph."""
    pipeline = app.state.pipeline
    queue = app.state.queue
    metrics = get_metrics()
    while True:
        lead = await queue.get()
        try:
            outcome = await pipeline.run(lead)
            metrics.record(outcome)
        except Exception:  # one bad lead must never kill the worker
            log.exception("worker.failed", lead_id=lead.id)
        finally:
            queue.task_done()


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level, pretty=settings.environment == "local")
    setup_tracing(settings)  # Langfuse LLM tracing if keys are set (else no-op)
    app.state.settings = settings
    app.state.pipeline = build_pipeline(settings)
    app.state.opportunity_pipeline = build_opportunity_pipeline(settings)
    app.state.queue = InMemoryQueue()  # per-app, bound to this event loop
    app.state.worker = asyncio.create_task(_consume(app))
    log.info("startup", demo_mode=settings.demo_mode, llm_enabled=settings.llm_enabled)
    try:
        yield
    finally:
        app.state.worker.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await app.state.worker


def create_app() -> FastAPI:
    app = FastAPI(
        title="BuildSignal GTM",
        version="0.2.0",
        summary="Multi-agent opportunity intelligence for building-material revenue teams.",
        lifespan=lifespan,
    )

    origins = get_settings().cors_allow_origin_list
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_methods=["GET", "POST"],
            allow_headers=["content-type"],
        )

    assets = _FRONTEND_DIST / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="frontend-assets")

    @app.get("/", response_class=HTMLResponse)
    async def demo() -> Response:
        frontend = _FRONTEND_DIST / "index.html"
        if frontend.is_file():
            return FileResponse(frontend)
        return HTMLResponse(build_demo_html())

    @app.get("/favicon.svg", include_in_schema=False)
    async def favicon() -> Response:
        icon = _FRONTEND_DIST / "favicon.svg"
        if icon.is_file():
            return FileResponse(icon, media_type="image/svg+xml")
        return Response(status_code=404)

    @app.get("/health")
    async def health() -> dict[str, object]:
        s = app.state.settings
        return {"status": "ok", "demo_mode": s.demo_mode, "queued": app.state.queue.qsize()}

    @app.post("/leads", status_code=202)
    async def ingest(
        request: Request,
        x_signature: str | None = Header(default=None),
    ) -> JSONResponse:
        body = await request.body()
        if not verify_signature(app.state.settings.webhook_signing_secret, body, x_signature):
            return JSONResponse({"error": "invalid signature"}, status_code=401)
        try:
            inbound = InboundLead.model_validate_json(body)
        except ValidationError:
            return JSONResponse({"error": "invalid lead payload"}, status_code=400)
        lead = normalize_lead(inbound)
        await app.state.queue.put(lead)  # 202: queued, worker handles the slow part
        return JSONResponse({"lead_id": lead.id, "status": "queued"}, status_code=202)

    @app.post("/leads/sync")
    async def ingest_sync(inbound: InboundLead) -> LeadOutcome:
        """Run the full pipeline inline — handy for demos, tests, and reviewers."""
        lead = normalize_lead(inbound)
        outcome: LeadOutcome = await app.state.pipeline.run(lead)
        get_metrics().record(outcome)
        return outcome

    @app.post("/opportunities/sync")
    async def analyze_opportunity(request: OpportunityRequest) -> OpportunityOutcome:
        """Run the BuildSignal specialist-agent graph and return an auditable sales brief."""
        outcome: OpportunityOutcome = await app.state.opportunity_pipeline.run(request)
        return outcome

    @app.get("/metrics")
    async def metrics() -> dict[str, object]:
        return get_metrics().snapshot()

    @app.get("/metrics/prometheus")
    async def metrics_prom() -> Response:
        return PlainTextResponse(get_metrics().prometheus())

    return app


app = create_app()

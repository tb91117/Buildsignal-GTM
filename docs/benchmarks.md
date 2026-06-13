# Benchmarks

> Methodology-first, and honest about what's measured vs. pending. Numbers marked _(pending)_ land
> when the LoRA classifier is trained — no placeholders are presented as results.

## Latency (measured)

Qualification runs in-process; the slow part (LLM drafting) is off the request path via the worker.
From the bundled `make demo` run (6 sample leads, rule qualifier, Apple Silicon, no network):

| Stage | p50 | p95 |
|-------|-----|-----|
| Qualify (rule baseline) | **~1.7 ms** | **~9.4 ms** |
| Draft (template, keyless) | <1 ms | <1 ms |
| Draft (LLM, network-bound) | _provider-dependent_ | _provider-dependent_ |

The point: the **decision** to respond is effectively instant; only the optional LLM text generation
costs real time, and it never blocks intake.

## Classifier quality _(pending — trained model)_

`make eval` compares three qualification strategies on a held-out set:

| Strategy | Macro-F1 | $/1k leads | Notes |
|----------|----------|-----------|-------|
| Rule baseline | _(pending)_ | **$0** | transparent, zero deps |
| LoRA-fine-tuned classifier | _(pending)_ | **~$0** | local inference, no per-call API cost |
| LLM zero-shot | _(pending)_ | _(metered)_ | strong but pays per lead, adds latency |

The thesis we're testing: a small fine-tuned classifier **matches or beats** LLM zero-shot on intent
while running locally for ~$0 and in single-digit milliseconds — the production-economics argument for
fine-tuning over prompting on a high-volume path.

## Cost framing (per 1,000 leads)

- **This tool (rule / LoRA path):** qualification is local → **~$0**. Cost is only incurred if you
  enable LLM drafting, and only on leads worth a personalized reply (not the spam you filtered).
- **Per-seat "instant response" SaaS:** typically billed per seat/month regardless of volume.

Self-hosting trades a SaaS subscription for your own compute — which, for the qualification path, is
effectively free.

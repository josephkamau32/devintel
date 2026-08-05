"""AI-specific Prometheus metrics.

These counters and histograms are incremented by the AIOrchestrator
on every completion and embedding request, giving full observability
into AI usage, latency, cost, and failure rates.
"""

from prometheus_client import Counter, Histogram

# ---------------------------------------------------------------------------
# Counters
# ---------------------------------------------------------------------------

ai_requests_total = Counter(
    "ai_requests_total",
    "Total AI requests",
    ["provider", "model", "agent", "operation", "status"],
)

ai_tokens_total = Counter(
    "ai_tokens_total",
    "Total tokens consumed",
    ["provider", "model", "token_type"],  # token_type: prompt | completion
)

ai_cost_estimate_usd = Counter(
    "ai_cost_estimate_usd_total",
    "Cumulative estimated cost in USD",
    ["provider", "model"],
)

ai_cache_hits_total = Counter(
    "ai_cache_hits_total",
    "AI response cache hits",
    ["operation"],
)

# ---------------------------------------------------------------------------
# Histograms
# ---------------------------------------------------------------------------

ai_request_duration_seconds = Histogram(
    "ai_request_duration_seconds",
    "AI request duration in seconds",
    ["provider", "model", "operation"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
)


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------


def record_ai_request(
    *,
    provider: str,
    model: str,
    agent: str,
    operation: str,
    status: str,
    latency_s: float,
    prompt_tokens: int,
    completion_tokens: int,
    cost_usd: float,
) -> None:
    """Record a completed AI request in all relevant metrics."""
    ai_requests_total.labels(
        provider=provider,
        model=model,
        agent=agent or "unknown",
        operation=operation,
        status=status,
    ).inc()

    ai_request_duration_seconds.labels(
        provider=provider, model=model, operation=operation
    ).observe(latency_s)

    if prompt_tokens:
        ai_tokens_total.labels(
            provider=provider, model=model, token_type="prompt"
        ).inc(prompt_tokens)

    if completion_tokens:
        ai_tokens_total.labels(
            provider=provider, model=model, token_type="completion"
        ).inc(completion_tokens)

    if cost_usd > 0:
        ai_cost_estimate_usd.labels(
            provider=provider, model=model
        ).inc(cost_usd)

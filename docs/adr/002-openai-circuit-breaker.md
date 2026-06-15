# ADR-002: Circuit Breaker Pattern for OpenAI API

## Status
Accepted

## Context
OpenAI API can experience outages, rate limiting, or network failures. Without protection, these failures cascade and cause:
- All requests to fail immediately
- Queue buildup in memory
- Poor user experience

## Decision
Implement a circuit breaker pattern with exponential backoff retries for all OpenAI API calls.

## Consequences
- **Positive**: Graceful degradation during outages
- **Positive**: Automatic recovery after failures
- **Positive**: Prevents cascading failures
- **Negative**: Additional complexity in error handling

## Implementation
- `OpenAICircuitBreaker` class in `app/integrations/openai_client.py`
- Failure threshold: 5 consecutive failures
- Recovery timeout: 60 seconds
- Uses `tenacity` for exponential backoff retries
- Handles `APITimeoutError`, `APIConnectionError`, `RateLimitError`

## Configuration
Circuit breaker parameters can be tuned via environment variables:
- `OPENAI_CIRCUIT_FAILURE_THRESHOLD`
- `OPENAI_CIRCUIT_RECOVERY_TIMEOUT`
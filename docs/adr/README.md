# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for DevIntel AI.

## Purpose

ADRs document significant architectural decisions made during development, including:
- The context and problem statement
- The decision made
- The consequences (positive and negative)
- Alternatives considered

## Format

Each ADR follows the template:
- Title
- Status (Proposed, Accepted, Deprecated, Superseded)
- Context
- Decision
- Consequences
- Alternatives Considered

## ADRs

1. [001-tree-sitter-chunking.md](./001-tree-sitter-chunking.md) - AST-aware semantic chunking strategy
2. [002-openai-circuit-breaker.md](./002-openai-circuit-breaker.md) - Resilience pattern for OpenAI API calls
3. [003-dual-authentication.md](./003-dual-authentication.md) - GitHub OAuth + Email/Password authentication
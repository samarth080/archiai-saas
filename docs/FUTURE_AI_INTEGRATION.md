# Future AI Integration Placeholder

> **Status:** Documentation only  
> **Runtime integration:** Disabled  
> **Current generator:** Deterministic rule engine with optional structured pattern data

## Purpose

ArchiAI may add optional AI-assisted layout workflows after the deterministic MVP is stable. This document records the intended integration boundary without enabling provider calls, model dependencies, API keys, paid services, or local model runtimes.

Sprint 11 does not call OpenAI, Claude, Gemini, Ollama, Hugging Face, or any other model provider.

## Potential Future Uses

AI assistance may be evaluated for:

- Turning loosely written design briefs into structured room requirements
- Ranking multiple deterministic layout candidates
- Suggesting refinement actions while keeping the user in control
- Learning aggregate, privacy-safe signals from explicitly approved layout edits
- Explaining layout-quality warnings in plain language

The existing deterministic generator remains the fallback path. AI output must be treated as advisory input and validated before it affects a saved design.

## Proposed Boundary

Future provider-specific integrations should live behind a small service interface separate from:

- Prompt extraction rules
- Deterministic layout generation
- Pattern-data access
- Layout-quality scoring
- Project persistence

The API layer may request an optional AI suggestion, but the layout engine should continue to accept structured requirements and resolved rules without knowing which provider produced them.

## Provider Options

Possible hosted providers:

- OpenAI
- Anthropic Claude
- Google Gemini

Possible local or self-hosted providers:

- Ollama
- Hugging Face-compatible runtimes

Provider selection must be configuration-driven. Secrets must come from environment variables and remain absent from committed files. No provider is configured or required in the current application.

## Required Controls Before Enablement

Before any provider integration is enabled, add:

- Explicit feature flags with AI disabled by default
- Environment-only secret configuration
- Input and output validation
- Timeouts, retry limits, and graceful deterministic fallback
- Cost budgets and rate limits for hosted providers
- Privacy review for prompts, saved layouts, and user edit signals
- Logging that records provider usage without logging secrets
- Tests for provider failures, malformed output, and fallback behavior

## Data Safety

Do not send private project data, personal data, scraped source content, or copyrighted floor-plan images to a model provider without an approved data policy and clear user-facing consent. Sprint 10 pattern records remain structured advisory data, not model-training data.

## Deferred Work

The following are intentionally outside Sprint 11:

- Hosted LLM API integration
- Local model runtime integration
- Fine-tuning or full model training
- Embeddings or vector search
- Automatic self-learning from user edits
- AI-generated CAD/BIM output
- Structural or code-compliance validation


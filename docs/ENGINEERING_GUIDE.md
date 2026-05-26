# Aetheris Engineering Guide

# 1. Purpose

This document defines the engineering standards, development workflow, architectural discipline, repository conventions, and implementation rules for Aetheris.

The goal of this guide is to ensure:

- consistency
- maintainability
- operational clarity
- predictable development
- scalable engineering discipline

This document is authoritative for implementation behavior and engineering practices.

---

# 2. Engineering Philosophy

Aetheris is engineered as:

- infrastructure-grade backend software
- modular and maintainable
- production-oriented from the beginning
- operationally observable
- scalable through measured evolution
- designed for long-term maintainability

The project intentionally avoids:

- premature microservices
- unnecessary infrastructure complexity
- speculative optimization
- architecture driven by trends instead of requirements

---

# 3. Development Priorities

Engineering priorities are ordered as follows:

1. correctness
2. security
3. observability
4. reliability
5. maintainability
6. developer experience
7. performance optimization later

Performance matters, but not at the cost of correctness or operational clarity.

---

# 4. Architectural Style

Aetheris uses:

- modular monolith architecture
- asynchronous worker processing
- vertical-slice implementation strategy

The codebase is organized around domains and workflows rather than technical-only layers.

---

# 5. Repository Structure

Recommended repository structure:

    /app
        /api
        /core
        /modules
        /workers
        /repositories
        /services
        /schemas
        /models
        /observability
        /tests

    /docs
    /scripts
    /migrations

    docker-compose.yml
    pyproject.toml
    README.md

---

# 6. Module Structure

Recommended module organization:

    modules/
        auth/
        organizations/
        api_keys/
        documents/
        ingestion/
        processing/
        embeddings/
        retrieval/
        generation/
        billing/
        observability/

Each module should remain:

- cohesive
- isolated
- explicit in responsibility

---

# 7. Layering Rules

Aetheris uses explicit layering.

Recommended layers:

- API layer
- service layer
- repository layer
- persistence layer

---

## 7.1 API Layer

Responsibilities:

- request validation
- authentication
- serialization
- HTTP concerns
- response formatting

The API layer must remain thin.

Business logic must not accumulate here.

---

## 7.2 Service Layer

Responsibilities:

- orchestration
- business rules
- workflow coordination
- transactional logic

This is the primary business logic layer.

---

## 7.3 Repository Layer

Responsibilities:

- persistence access
- query encapsulation
- database interaction

Repositories should not contain business rules.

---

## 7.4 Worker Layer

Responsibilities:

- asynchronous processing
- retries
- ingestion workflows
- vector indexing
- cleanup tasks

Workers must remain:

- idempotent
- observable
- retry-safe

---

# 8. Coding Standards

# 8.1 Python Version

Recommended baseline:

- Python 3.12+

---

# 8.2 Typing

All production code should use:

- explicit typing
- strict type awareness

Pyright should pass cleanly.

Avoid untyped public interfaces.

---

# 8.3 Style Rules

Use:

- Ruff
- Ruff formatter

Avoid maintaining separate formatter stacks unless necessary.

---

# 8.4 Naming Conventions

Use explicit names.

Examples:

Good:

- document_processing_service
- generate_embeddings
- organization_repository

Avoid vague names such as:

- helper
- manager
- util
- processor2

---

# 8.5 Function Design

Functions should remain:

- small
- composable
- deterministic where practical
- single-purpose

Avoid giant orchestration functions.

---

# 8.6 Comments

Comments should explain:

- intent
- reasoning
- non-obvious constraints

Avoid comments that restate the code mechanically.

---

# 8.7 Constants

Avoid magic values in implementation logic.

Centralize:

- limits
- statuses
- enums
- configuration defaults

---

# 9. Configuration Standards

Configuration must be environment-driven.

Use:

- environment variables
- Pydantic Settings
- `.env` locally only

---

## 9.1 Environment Separation

Separate environments:

- development
- testing
- staging
- production

Never share secrets between environments.

---

## 9.2 Secret Handling

Secrets must never:

- exist in Git
- appear in logs
- appear in exception traces

Use secret managers in production environments.

---

# 10. Git Workflow

# 10.1 Branching Strategy

Main branches:

- main
- develop (optional if needed later)

Feature branches:

    feature/upload-pipeline
    feature/search-endpoint

Fix branches:

    fix/job-retry-loop

Refactor branches:

    refactor/vector-service

---

# 10.2 Pull Request Rules

PRs should remain:

- focused
- reviewable
- reasonably small

Avoid:

- unrelated changes
- giant architectural rewrites
- mixed-purpose PRs

---

# 10.3 Commit Rules

Commits should be:

- atomic
- understandable
- traceable

Examples:

    feat: implement document upload pipeline
    fix: prevent duplicate chunk indexing
    refactor: split retrieval orchestration service

---

# 10.4 Main Branch Protection

The main branch should require:

- passing CI
- successful tests
- linting
- type checks

Direct pushes to main are discouraged.

---

# 11. Testing Standards

# 11.1 Testing Philosophy

Aetheris uses:

- unit tests
- integration tests
- focused e2e tests

Priority order:

1. unit tests
2. integration tests
3. e2e tests

---

# 11.2 Unit Tests

Unit tests should isolate:

- services
- validators
- utilities
- orchestration logic

External providers should be mocked.

---

# 11.3 Integration Tests

Integration tests should validate:

- PostgreSQL
- Redis
- Qdrant
- object storage
- migrations

Use real containers where practical.

---

# 11.4 RAG Evaluation

RAG quality testing should validate:

- retrieval quality
- citation grounding
- hallucination resistance
- insufficient-context handling

---

# 11.5 Regression Testing

Major bugs should produce:

- regression tests

This prevents repeated operational failures.

---

# 12. Observability Standards

# 12.1 Structured Logging

All services must emit:

- structured JSON logs

Required metadata includes:

- request_id
- trace_id
- tenant_id
- user_id
- job_id

---

# 12.2 OpenTelemetry

OpenTelemetry instrumentation should exist across:

- HTTP requests
- workers
- database queries
- vector retrieval
- provider calls

---

# 12.3 Error Visibility

Failures must become:

- observable
- searchable
- diagnosable

Silent failures are unacceptable.

---

# 13. Async Processing Standards

# 13.1 Queue Philosophy

Long-running work must be asynchronous.

Examples:

- extraction
- chunking
- embedding generation
- indexing

---

# 13.2 Idempotency

Worker tasks must remain:

- idempotent

Retries must not corrupt state.

---

# 13.3 Retry Strategy

Retry only transient failures.

Do not retry:

- invalid uploads
- malformed documents
- permanent validation failures

---

# 13.4 Job State Management

Jobs must expose explicit states:

- QUEUED
- PROCESSING
- COMPLETED
- FAILED
- CANCELLED

---

# 14. API Standards

# 14.1 Versioning

All APIs must be versioned.

Example:

    /api/v1/

---

# 14.2 Response Consistency

Responses must follow stable structures.

Errors must remain machine-readable.

---

# 14.3 Tenant Enforcement

Every endpoint must enforce:

- organization boundaries

Tenant isolation is non-negotiable.

---

# 15. Database Standards

# 15.1 Migrations

All schema changes require:

- Alembic migrations

No manual production schema mutation.

---

# 15.2 Soft Deletion

Prefer:

- soft deletion
- asynchronous cleanup

over destructive immediate deletion.

---

# 15.3 Query Design

Optimize queries for:

- tenant scoping
- pagination
- predictable performance

---

# 16. Security Standards

# 16.1 Authentication

Use:

- JWT access tokens
- rotating refresh tokens
- hashed API keys

---

# 16.2 Rate Limiting

All public APIs require:

- rate limiting

---

# 16.3 Upload Validation

Uploads must validate:

- file size
- MIME type
- extension
- malformed payloads

---

# 16.4 Secret Hygiene

Secrets must never:

- enter source control
- appear in logs
- appear in screenshots/documentation

---

# 17. Reliability Philosophy

The platform should fail:

- visibly
- predictably
- recoverably

not silently.

---

# 17.1 Graceful Degradation

Provider failures should degrade functionality gracefully where practical.

---

# 17.2 Eventual Consistency

Eventual consistency between:

- PostgreSQL
- Qdrant
- object storage

is acceptable and intentional.

---

# 17.3 Recovery

The system should support:

- retries
- reindexing
- reprocessing
- rebuildability

---

# 18. Technical Debt Policy

Technical debt must remain:

- explicit
- documented
- intentional

Avoid hidden architectural decay.

---

# 18.1 Temporary Workarounds

Temporary solutions must include:

- rationale
- removal intent
- tracking reference if applicable

---

# 18.2 Refactoring

Refactor continuously and incrementally.

Avoid massive rewrites.

---

# 19. Documentation Standards

Documentation should evolve with architecture.

Important changes should update:

- architecture docs
- API docs
- operational docs

---

# 19.1 ADRs

Major decisions should produce lightweight ADRs.

Examples:

- infrastructure shifts
- provider changes
- architectural reversals

---

# 20. Performance Philosophy

Performance optimization should follow:

- profiling
- operational evidence
- measured bottlenecks

Avoid speculative optimization.

---

# 21. Deployment Philosophy

Local development should resemble production architecture where practical.

The architecture should remain compatible with future AWS deployment without requiring architectural rewrites.

---

# 22. Engineering Invariants

The following are mandatory engineering invariants:

- every tenant boundary must be explicit
- every long-running task must be asynchronous
- every worker task must be idempotent
- every critical failure must be observable
- every public endpoint must be versioned
- every migration must be reproducible
- every secret must stay outside Git
- every major bug should produce a regression test

---

# 23. Summary

This guide defines the engineering discipline behind Aetheris. The platform prioritizes correctness, observability, maintainability, and long-term scalability while intentionally avoiding premature infrastructure complexity.

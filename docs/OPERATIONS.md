# Aetheris Operations Guide

# 1. Purpose

This document defines the operational standards, local environment setup, deployment workflow, observability configuration, runtime management, and recovery principles for Aetheris.

The goal is to ensure:

- reproducible environments
- operational clarity
- production readiness
- reliable deployments
- observable runtime behavior

---

# 2. Operational Philosophy

Aetheris operations prioritize:

- simplicity
- reproducibility
- observability
- recoverability
- production realism

The operational model intentionally avoids unnecessary infrastructure complexity during the MVP phase.

---

# 3. Runtime Components

Aetheris consists of the following runtime components:

- API service
- worker service
- PostgreSQL
- Redis
- Qdrant
- MinIO
- Nginx

All components are containerized.

---

# 4. Local Development Environment

# 4.1 Local Stack

The local development stack should closely resemble production architecture.

Recommended local services:

- API container
- worker container
- PostgreSQL container
- Redis container
- Qdrant container
- MinIO container
- Nginx container

---

# 4.2 Local Orchestration

Use:

- Docker Compose

for local orchestration.

Recommended startup command:

    docker compose up --build

---

# 4.3 Local Environment Goals

The local environment should support:

- full ingestion flow
- semantic retrieval
- background workers
- object storage
- observability testing

without requiring cloud infrastructure.

---

# 5. Environment Configuration

# 5.1 Environment Variables

Configuration should be environment-driven.

Examples:

- database URLs
- Redis URLs
- provider keys
- JWT secrets
- object storage credentials

---

# 5.2 Environment Files

Use:

- `.env`

for local development only.

Production secrets must come from secure secret management systems.

---

# 5.3 Environment Separation

Maintain separate configurations for:

- development
- testing
- staging
- production

Never reuse production secrets in lower environments.

---

# 6. Docker Standards

# 6.1 Container Philosophy

Containers should remain:

- single-purpose
- reproducible
- stateless where possible

---

# 6.2 Image Standards

Use:

- minimal base images
- deterministic dependency installation

Avoid unnecessary packages.

---

# 6.3 Dependency Reproducibility

Dependencies should be:

- pinned
- reproducible
- version-controlled

---

# 7. Database Operations

# 7.1 Migration Tooling

Use:

- Alembic

for all schema evolution.

---

# 7.2 Migration Execution

Migrations should execute:

- automatically in CI validation
- explicitly during deployment

Avoid manual schema mutation.

---

# 7.3 Database Backups

Critical backup targets:

- PostgreSQL
- object storage

Qdrant indexes are rebuildable.

---

# 7.4 Database Recovery

Recovery priorities:

1. correctness
2. tenant safety
3. auditability
4. operational continuity

---

# 8. Object Storage Operations

# 8.1 Local Storage

Use:

- MinIO

for local development.

---

# 8.2 Production Storage

Recommended production direction:

- S3-compatible object storage

Future AWS target:

- Amazon S3

---

# 8.3 Artifact Preservation

Retain:

- original uploads
- extracted text
- preprocessing artifacts

This enables:

- debugging
- audits
- reprocessing
- provider migration

---

# 9. Worker Operations

# 9.1 Worker Responsibilities

Workers process:

- extraction
- chunking
- embedding generation
- indexing
- cleanup
- reprocessing

---

# 9.2 Worker Scaling

Workers should scale horizontally.

The API layer and worker layer are independently scalable.

---

# 9.3 Retry Handling

Retries should target transient failures only.

Permanent validation failures should terminate explicitly.

---

# 9.4 Idempotency

Worker tasks must remain idempotent.

Duplicate execution must not corrupt state.

---

# 10. Observability Operations

# 10.1 Logging

All runtime services emit:

- structured JSON logs

Required metadata:

- request_id
- trace_id
- tenant_id
- user_id
- job_id

---

# 10.2 OpenTelemetry

OpenTelemetry instrumentation should cover:

- API requests
- Celery workers
- database interactions
- vector retrieval
- provider calls

---

# 10.3 Monitoring Philosophy

Monitoring exists to answer:

- what failed
- where it failed
- why it failed
- for which tenant
- for which request

without manual reconstruction.

---

# 10.4 Error Visibility

Critical failures must become:

- observable
- searchable
- diagnosable

Silent operational failures are unacceptable.

---

# 11. Health Checks

# 11.1 Health Endpoint

Purpose:

- process liveness

Example:

    GET /api/v1/health

---

# 11.2 Readiness Endpoint

Purpose:

- dependency validation

Checks may include:

- PostgreSQL connectivity
- Redis availability
- Qdrant availability
- object storage availability

---

# 12. Security Operations

# 12.1 HTTPS

Production traffic must use:

- HTTPS only

---

# 12.2 Secret Management

Secrets must never:

- exist in Git
- appear in logs
- appear in screenshots
- appear in exception traces

---

# 12.3 API Key Handling

API keys should:

- be shown once
- remain hashed at rest
- be revocable

---

# 12.4 Rate Limiting

All public endpoints require:

- rate limiting

to reduce abuse risk.

---

# 13. CI/CD Operations

# 13.1 CI Requirements

CI pipelines should validate:

- linting
- formatting
- typing
- tests
- migrations

---

# 13.2 Deployment Philosophy

Deployments should be:

- repeatable
- automated
- observable

Avoid manual production mutations.

---

# 13.3 Main Branch Rules

The main branch should require:

- successful CI
- passing tests
- successful static analysis

before merges.

---

# 14. Production Deployment Direction

# 14.1 Initial Deployment Model

The MVP deployment model is container-based.

---

# 14.2 AWS Direction

Future AWS compatibility includes:

- ECS/Fargate
- RDS
- S3
- ElastiCache
- CloudWatch

---

# 14.3 Kubernetes Strategy

Kubernetes is intentionally deferred until operational scale justifies it.

---

# 15. Recovery & Reliability

# 15.1 Failure Philosophy

The system should fail:

- visibly
- predictably
- recoverably

not silently.

---

# 15.2 Eventual Consistency

Eventual consistency between:

- PostgreSQL
- Qdrant
- object storage

is intentional.

---

# 15.3 Reprocessing

Documents should support:

- re-chunking
- re-embedding
- reindexing

without re-uploading.

---

# 16. Operational Runbooks

Important operational procedures should eventually include:

- local environment recovery
- migration rollback
- queue recovery
- object storage recovery
- reindexing workflows

---

# 17. Scaling Philosophy

Scaling should follow:

- measured bottlenecks
- operational evidence
- profiling data

Avoid speculative infrastructure scaling.

---

# 18. Operational Invariants

The following are mandatory operational invariants:

- every environment must be reproducible
- every deployment must be observable
- every critical failure must be diagnosable
- every worker task must remain idempotent
- every tenant boundary must remain enforceable
- every production secret must remain externalized
- every schema change must be migration-driven

---

# 19. Summary

This guide defines the operational foundations for Aetheris. The operational model prioritizes reproducibility, observability, reliability, and future production scalability while intentionally remaining lean and maintainable during the MVP stage.

# ADR 003: Use Redis and Celery for Background Processing

## Status
Accepted

## Date
2026-05-26

## Context

Aetheris must process document uploads asynchronously because document ingestion includes work that is too slow for synchronous HTTP request handling, such as:

- file extraction
- text normalization
- chunking
- embedding generation
- vector indexing
- cleanup and reprocessing

The platform must preserve low latency for API requests while still supporting reliable background processing.

Candidate approaches include:

- synchronous request processing
- custom background threads
- a task queue with workers
- a full distributed event streaming platform

The MVP needs a solution that is reliable, Python-friendly, easy to operate locally, and scalable enough for future growth.

## Decision

Aetheris will use **Redis** as the queue backend and **Celery** as the background task processing system.

The API service will enqueue long-running jobs, and Celery workers will process them asynchronously.

## Rationale

### Why Celery

Celery is a mature and widely adopted task processing framework for Python. It fits the project’s need for:

- asynchronous job execution
- retry policies
- task chaining
- separation of request handling from heavy work
- worker scaling
- clear operational boundaries

Celery is a practical choice for a Python backend that needs reliable background orchestration without designing a custom task system.

### Why Redis

Redis is a simple and effective fit for:

- task queue transport
- rate limiting support
- transient coordination
- lightweight caching
- local Docker-based development

Redis keeps the stack simple and is easy to run locally while remaining common in production environments.

### Why not synchronous processing

Document processing can be slow and variable. Synchronous handling would:

- increase API latency
- tie up request workers
- reduce reliability under load
- make failures harder to isolate
- degrade the user experience

### Why not a Kafka/RabbitMQ-first design

A message streaming platform is unnecessary for the MVP. It would add operational complexity that is not justified by the current scale or by the need for rapid implementation.

Celery with Redis gives the right balance of practicality and control.

## Consequences

### Positive consequences

- API responses stay fast.
- Long-running work is isolated from HTTP request handling.
- Retries and worker failures are manageable.
- Background processing can be scaled independently.
- Local development remains straightforward.

### Negative consequences

- Celery introduces operational state that must be monitored.
- Queue jobs must be designed carefully for idempotency.
- Eventually consistent processing means the job state must be tracked explicitly.
- Worker code must be disciplined to avoid duplicate processing.

## Implementation Rules

1. The HTTP API must never block on document extraction or embedding generation.
2. Every long-running workflow must be represented as a task or task chain.
3. Jobs must be idempotent.
4. Retryable failures must be separated from permanent failures.
5. Job state must be persisted in PostgreSQL.
6. Every job must carry tenant context.
7. Task execution must emit structured logs and trace metadata.

## Required Use Cases

Celery must be used for:

- document ingestion workflows
- extraction and chunking
- embedding generation
- vector indexing
- document deletion cleanup
- document reprocessing
- reindexing

## Retry and Failure Policy

- Transient external failures may be retried with bounded backoff.
- Invalid files or permanent parsing errors must fail explicitly.
- Failed jobs must preserve error metadata.
- Duplicate execution must not create duplicate chunks or duplicate vector entries.

## Alternatives Considered

### Synchronous processing
Rejected because it would make the API slow and unreliable.

### Custom background threads
Rejected because it would be harder to observe, retry, and scale correctly.

### Kafka or RabbitMQ as the initial backbone
Rejected as too much operational complexity for the MVP.

## Validation

This decision is valid if:

- uploads return quickly
- workers process reliably
- job states are visible
- retries are safe
- local setup remains easy
- worker throughput can grow independently of the API

## Related Decisions

- Modular monolith architecture
- PostgreSQL for persistent job state
- Qdrant for vector indexing
- OpenTelemetry for tracing

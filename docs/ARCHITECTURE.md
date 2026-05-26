# Aetheris Architecture

## 1. Purpose

This document defines the architecture of Aetheris API: a multi-tenant, headless backend for document ingestion, semantic retrieval, and retrieval-augmented generation. It is the authoritative reference for system boundaries, data flow, component responsibilities, and the design constraints that shape implementation.

## 2. Architectural goals

Aetheris is designed to be:

- API-first
- multi-tenant
- modular
- asynchronous
- observable
- secure by default
- production-oriented
- suitable for future SaaS monetization
- maintainable by a small team
- ready for horizontal worker scaling
- extensible without premature microservice complexity

## 3. Architectural style

Aetheris uses a modular monolith architecture with asynchronous workers.

The system is intentionally not split into many microservices at the MVP stage. Instead, it is organized into domain modules that are cleanly separated in code and in responsibility, while still running in one deployable application plus background workers.

### Why this style

This architecture was chosen to balance:

- maintainability
- development speed
- operational simplicity
- testability
- future extractability
- low infrastructure overhead

### What it is not

Aetheris is not designed as:

- a frontend product
- a microservices platform from day one
- a Kubernetes-first system
- a distributed event mesh for its own sake
- a generic AI agent framework

## 4. Technology stack

### Web API
- FastAPI

### Relational database
- PostgreSQL

### ORM
- SQLAlchemy 2.0

### Migrations
- Alembic

### Queue and worker system
- Redis
- Celery

### Vector database
- Qdrant

### Object storage
- MinIO locally
- AWS S3-compatible storage in production

### Reverse proxy
- Nginx

### Configuration
- Pydantic Settings
- environment variables
- `.env` files for local development

### Logging and telemetry
- structured JSON logs
- OpenTelemetry-ready tracing

### Testing
- Pytest

### Static analysis and formatting
- Ruff
- Pyright

## 5. High-level system boundary

Aetheris consists of the following major runtime components:

- API service
- worker service
- PostgreSQL
- Redis
- Qdrant
- object storage
- reverse proxy

These components are containerized and orchestrated locally with Docker Compose.

## 6. Domain modules

The codebase is organized around domain modules rather than purely technical layers.

Recommended modules:

- auth
- organizations
- api_keys
- documents
- ingestion
- processing
- embeddings
- retrieval
- generation
- billing
- observability
- common

### Module responsibilities

#### auth
Authentication, tokens, login, identity, and session handling.

#### organizations
Organizations, membership, and tenant ownership boundaries.

#### api_keys
Organization-scoped API key generation, hashing, revocation, and metadata.

#### documents
Document metadata, document lifecycle state, version awareness, soft delete behavior, and document-scoped queries.

#### ingestion
Upload handling, validation, file hashing, object storage upload, job creation, and enqueueing.

#### processing
Asynchronous document processing orchestration, extraction, cleaning, chunking, and pipeline state transitions.

#### embeddings
Embedding generation, provider abstraction, embedding validation, and persistence of embedding metadata.

#### retrieval
Semantic search, metadata filtering, ranking, and retrieval result assembly.

#### generation
Prompt construction, context assembly, LLM provider abstraction, and grounded answer generation with citations.

#### billing
Usage tracking foundations and future billing readiness. Billing logic is not part of the MVP implementation, but the architecture must remain compatible with it.

#### observability
Structured logging, tracing helpers, correlation propagation, metrics hooks, and instrumentation conventions.

#### common
Shared utilities, base schemas, constants, errors, and low-level helpers that should not belong to a specific domain.

## 7. Request and processing model

### 7.1 API request model

The public API is REST-first and versioned under `/api/v1/`.

The API is designed to be externally consumable from day one, even if initial deployment is private.

Important API principles:

- resource-oriented routes
- stable request and response shapes
- consistent error format
- predictable pagination behavior
- authentication via JWT or API key
- explicit tenant scoping
- OpenAPI as the canonical machine-readable contract

### 7.2 Asynchronous processing model

Long-running work must never block the HTTP request path.

Examples of work that must be asynchronous:

- file parsing
- text extraction
- chunking
- embedding generation
- vector indexing
- cleanup
- reindexing

The HTTP layer is responsible only for validation, metadata creation, object storage upload, and job enqueueing.

### 7.3 Job model

Jobs are used to manage asynchronous work.

Typical job states:

- QUEUED
- PROCESSING
- COMPLETED
- FAILED
- CANCELLED

Jobs must be:

- retryable
- idempotent
- observable
- auditable

## 8. Core workflows

### 8.1 Document upload workflow

1. Client authenticates with a JWT or API key.
2. Client uploads a PDF, TXT, or Markdown file.
3. API validates the request.
4. API stores the original file in object storage.
5. API creates document metadata in PostgreSQL.
6. API creates a job record and enqueues a worker task.
7. A worker processes the document asynchronously.
8. The worker extracts text, cleans it, chunks it, generates embeddings, and stores vectors in Qdrant.
9. The job is marked completed or failed.

### 8.2 Semantic search workflow

1. Client submits a query.
2. The query is embedded.
3. Qdrant returns relevant chunks.
4. Metadata filters restrict results to the correct tenant and optional query filters.
5. The API returns retrieved chunks, scores, and citations.

### 8.3 Ask workflow

1. Client submits a question.
2. The system runs retrieval.
3. The system assembles the best context window from retrieved chunks.
4. The configured LLM provider generates a grounded answer.
5. The response includes the answer, citations, and retrieved chunks.

## 9. Data and storage architecture

### 9.1 PostgreSQL responsibilities

PostgreSQL stores:

- organizations
- users
- memberships
- API keys
- documents
- document versions
- chunks
- jobs
- job events
- query logs
- generated answers
- citations
- usage records
- audit records

### 9.2 Qdrant responsibilities

Qdrant stores semantic vectors and searchable metadata for chunks.

Vector payloads must include at least:

- organization_id
- document_id
- chunk_id
- page metadata
- section metadata
- timestamps
- embedding version information

### 9.3 Object storage responsibilities

Object storage stores:

- original uploaded files
- extracted raw text
- preprocessing outputs
- chunk manifests
- derived artifacts

Recommended logical organization:

- organization
- document
- artifact type

This allows recovery, reprocessing, and debugging without re-uploading the source file.

## 10. Multi-tenancy model

Aetheris is multi-tenant from day one.

### Tenancy boundaries

All access to:

- documents
- chunks
- jobs
- queries
- generated answers
- usage data
- audit records

must be scoped to an organization.

### Tenant enforcement

Tenant scoping must be enforced:

- in API handlers
- in services
- in repositories
- in worker tasks
- in retrieval queries
- in cleanup jobs

Tenant isolation is not optional and must not depend on implicit trust.

## 11. Security model

Security principles:

- HTTPS-only production traffic
- JWT access tokens for user sessions
- rotating refresh tokens
- organization-scoped API keys
- hashed API key storage
- strong tenant enforcement
- rate limiting
- strict logging hygiene
- secrets never committed to Git
- validation of uploaded input
- no raw secrets in logs

### API keys

API keys are visible only once at creation time and are stored only as hashes thereafter.

### Passwords

User passwords must be hashed securely. The implementation should use modern password hashing appropriate for the chosen Python ecosystem.

## 12. Observability model

Aetheris is built to be observable from the beginning.

### Logging

All services emit structured JSON logs.

Core correlation fields include:

- request_id
- trace_id
- tenant_id
- user_id
- job_id

### Tracing

OpenTelemetry-compatible tracing must be supported across:

- HTTP requests
- worker tasks
- database operations
- vector search
- embedding generation
- LLM calls

### Observability principle

Observability must answer:

- what failed
- where it failed
- why it failed
- for which tenant
- for which request
- for which job

without manual reconstruction.

## 13. Reliability model

Aetheris is designed for graceful failure and controlled recovery.

### Reliability requirements

- background failures must not crash the API
- jobs must be retryable
- worker tasks must be idempotent
- terminal job failure states must be explicit
- readiness checks must validate critical dependencies
- recovery and reindexing workflows must be supported

### Failure handling

System failures should be observable and recoverable, not silent.

### Eventual consistency

The system accepts eventual consistency between PostgreSQL, Qdrant, and object storage.

This is intentional and required for practical async processing.

## 14. Local development architecture

Local development is Docker Compose centered.

Typical local stack:

- API
- worker
- PostgreSQL
- Redis
- Qdrant
- MinIO
- Nginx

Local development should resemble production architecture closely enough to catch integration issues early, while still being easy to run with a single command.

## 15. Deployment architecture

The initial operational model is container-based.

### Local or self-hosted MVP

The platform should run in containers and be able to start locally with Docker Compose.

### Future AWS direction

The architecture is compatible with future AWS deployment using services such as:

- ECS/Fargate
- RDS
- S3
- ElastiCache
- CloudWatch

Kubernetes is intentionally deferred.

## 16. Development philosophy

Aetheris should be built using:

- vertical slices
- small focused pull requests
- tests alongside implementation
- explicit documentation updates
- incremental refactoring
- measured scaling decisions
- no premature microservices
- no speculative platform complexity

## 17. MVP exclusions

The architecture intentionally excludes the following from the MVP:

- OCR
- frontend UI
- SSO/SAML
- streaming responses
- reranking
- hybrid retrieval
- multimodal ingestion
- advanced billing logic
- agent workflows
- Kubernetes

These features can be added later without redesigning the core architecture.

## 18. Future readiness

The architecture remains compatible with future growth in these directions:

- SaaS billing
- enterprise SSO
- stronger tenant isolation
- knowledge bases or workspaces
- advanced observability
- retrieval reranking
- streaming LLM responses
- dedicated enterprise deployments
- region-aware infrastructure
- audit and compliance maturity

## 19. Design invariants

The following are non-negotiable design invariants:

- Every tenant boundary must be explicit.
- Every long-running task must be asynchronous.
- Every worker task must be idempotent.
- Every meaningful business decision must be testable.
- Every public API contract must be stable and versioned.
- Every critical failure must be observable.
- Every document-processing stage must be recoverable.
- Every production secret must stay out of the repository.

## 20. Summary

Aetheris is a modular, API-first, multi-tenant backend for enterprise document retrieval and RAG. The architecture is deliberately lean, professional, and scalable without premature complexity. It is designed to support a production-grade MVP now and a SaaS platform later.


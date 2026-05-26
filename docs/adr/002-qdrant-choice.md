# ADR 002: Use Qdrant as the Vector Database

## Status
Accepted

## Date
2026-05-26

## Context

Aetheris needs a vector database to support semantic search and retrieval for document chunks. The vector store must:

- work locally during development
- be production-capable
- support metadata filtering
- be fast for similarity search
- integrate cleanly with a Python backend
- remain practical for future SaaS usage
- support tenant-aware retrieval

The candidate options considered were:

- PostgreSQL with vector extensions
- a managed vector database
- a self-hosted open-source vector database

The selected system must fit a modular monolith architecture and support a future path to AWS deployment.

## Decision

Aetheris will use **Qdrant** as the vector database.

In the MVP, Qdrant will be self-hosted locally through Docker Compose and integrated directly into the backend through the Python application layer.

## Rationale

### Why Qdrant

Qdrant is a strong fit because it provides:

- open-source availability
- straightforward local deployment
- strong similarity-search performance
- metadata filtering
- practical Python integration
- production readiness
- compatibility with a future self-hosted or cloud-hosted deployment model

It fits the project’s need for an enterprise-style backend without forcing early managed service dependency.

### Why not PostgreSQL vector storage for the primary vector layer

PostgreSQL is the authoritative transactional store, but it is not the best primary semantic retrieval engine for this project.

Using PostgreSQL as the main vector engine would:

- couple semantic retrieval too tightly to the relational store
- reduce retrieval specialization
- limit the clarity of the persistence model
- make future scaling of vector search less explicit

PostgreSQL may still hold chunk metadata, audit data, and operational records, but not the primary vector search index.

### Why not a managed vector database first

A managed service would add cost, vendor dependence, and environment fragmentation too early. The project explicitly needs a free, local-first, production-readable stack.

Qdrant gives the best balance of cost, capability, and operational control.

## Consequences

### Positive consequences

- Local development is realistic and production-like.
- Retrieval logic is explicit and isolated.
- Vector indexing can be rebuilt from source artifacts.
- Metadata filters can enforce tenant boundaries.
- The architecture remains portable and open-source friendly.

### Negative consequences

- Qdrant must be operationally maintained as part of the stack.
- Data consistency between PostgreSQL, object storage, and Qdrant is eventually consistent rather than strictly transactional.
- The system must implement careful reindexing and recovery logic.

## Implementation Rules

1. Every embedded chunk must have a stable identifier.
2. Every vector payload must include tenant metadata.
3. Every retrieval query must filter by organization.
4. Vector records must be rebuildable from source documents and stored chunk metadata.
5. Embedding version information must be stored explicitly.
6. Reindexing must be supported as a normal operational workflow.

## Data Model Expectations

Qdrant payloads must contain at least:

- organization_id
- document_id
- chunk_id
- chunk_index
- embedding_model
- embedding_version
- page_number
- source metadata
- created_at

## Operational Notes

- Qdrant will be started locally with Docker Compose.
- Qdrant will be read and written only through the application layer.
- Vector data should be treated as rebuildable, not the sole source of truth.
- PostgreSQL remains the authoritative store for document metadata and job state.

## Alternatives Considered

### PostgreSQL with vector extension
Rejected as the primary vector layer because the project needs a dedicated semantic retrieval engine and a clearer split between transactional data and vector search.

### Managed vector service
Rejected for MVP due to cost and operational dependency.

## Validation

This decision is valid if:

- semantic search remains fast and stable
- tenant filtering works correctly
- reindexing is operationally possible
- local development remains simple
- production deployment remains feasible without re-architecture

## Related Decisions

- Multi-tenant modular monolith architecture
- PostgreSQL as the system of record
- Redis and Celery for async pipeline jobs
- Object storage for raw and derived document artifacts

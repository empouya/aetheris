# Aetheris Database Design

# 1. Purpose

This document defines the persistence architecture for Aetheris, including:

- relational schema design
- vector storage strategy
- object storage organization
- indexing philosophy
- tenant isolation model
- persistence invariants

Aetheris uses a poly-storage architecture composed of:

- PostgreSQL
- Qdrant
- object storage

Each storage system has explicit responsibilities.

---

# 2. Persistence Principles

The persistence layer must be:

- multi-tenant
- auditable
- scalable
- observable
- recoverable
- migration-friendly
- operationally debuggable

Important principles:

- tenant boundaries are explicit
- source documents are preserved
- derived artifacts are reproducible
- vector indexing is rebuildable
- soft deletion is preferred over destructive deletion

---

# 3. Storage Systems

## 3.1 PostgreSQL Responsibilities

PostgreSQL stores:

- users
- organizations
- memberships
- API keys
- documents
- processing jobs
- query logs
- usage records
- audit metadata
- chunk metadata
- generated answer metadata

PostgreSQL is the authoritative transactional source of truth.

---

## 3.2 Qdrant Responsibilities

Qdrant stores:

- semantic embeddings
- vector payload metadata
- retrieval indexes

Qdrant is optimized for:

- semantic similarity search
- filtered retrieval
- scalable vector operations

---

## 3.3 Object Storage Responsibilities

Object storage stores:

- original uploaded files
- extracted text artifacts
- preprocessing outputs
- chunk manifests
- derived artifacts

Recommended providers:

- MinIO locally
- S3-compatible storage in production

---

# 4. Multi-Tenant Design

## 4.1 Tenant Boundary

The organization is the primary tenant boundary.

Every major resource references:

- organization_id

---

## 4.2 Tenant Enforcement

Tenant filtering must exist:

- in queries
- in repositories
- in worker tasks
- in retrieval operations
- in cleanup jobs

Tenant isolation must never rely on client trust.

---

# 5. Core Relational Entities

# 5.1 organizations

Purpose:

- top-level tenant container

Important fields:

- id
- name
- slug
- created_at
- updated_at
- deleted_at

Indexes:

- unique slug

---

# 5.2 users

Purpose:

- authenticated user identities

Important fields:

- id
- email
- password_hash
- is_active
- created_at
- updated_at

Indexes:

- unique email

---

# 5.3 memberships

Purpose:

- organization membership mapping

Important fields:

- id
- organization_id
- user_id
- role
- created_at

Roles:

- owner
- admin
- member

Indexes:

- organization_id
- user_id
- unique organization/user pair

---

# 5.4 api_keys

Purpose:

- organization-scoped programmatic access

Important fields:

- id
- organization_id
- name
- key_prefix
- key_hash
- last_used_at
- revoked_at
- created_at

Important notes:

- plaintext keys are never stored
- hashes only

Indexes:

- organization_id
- key_prefix

---

# 5.5 documents

Purpose:

- uploaded document metadata

Important fields:

- id
- organization_id
- filename
- content_type
- file_size
- object_storage_path
- checksum
- status
- uploaded_by_user_id
- created_at
- updated_at
- deleted_at

Possible statuses:

- UPLOADED
- PROCESSING
- READY
- FAILED
- DELETED

Indexes:

- organization_id
- status
- created_at
- checksum

---

# 5.6 processing_jobs

Purpose:

- async workflow tracking

Important fields:

- id
- organization_id
- document_id
- job_type
- status
- retry_count
- error_message
- created_at
- started_at
- completed_at

Possible statuses:

- QUEUED
- PROCESSING
- COMPLETED
- FAILED
- CANCELLED

Indexes:

- organization_id
- status
- document_id
- created_at

---

# 5.7 document_chunks

Purpose:

- chunk metadata tracking

Important fields:

- id
- organization_id
- document_id
- chunk_index
- token_count
- text_hash
- metadata_json
- created_at

Important note:

Chunk text itself may optionally remain in PostgreSQL for debugging and auditing, even though semantic retrieval happens in Qdrant.

Indexes:

- organization_id
- document_id
- chunk_index

---

# 5.8 query_logs

Purpose:

- observability
- analytics
- future billing compatibility

Important fields:

- id
- organization_id
- user_id
- query_text
- endpoint_type
- latency_ms
- created_at

Indexes:

- organization_id
- created_at
- endpoint_type

---

# 5.9 generated_answers

Purpose:

- optional answer persistence
- debugging
- auditing
- evaluation

Important fields:

- id
- organization_id
- query_log_id
- answer_text
- provider_name
- model_name
- created_at

Indexes:

- organization_id
- query_log_id

---

# 5.10 usage_records

Purpose:

- billing readiness
- quota enforcement
- analytics

Important fields:

- id
- organization_id
- usage_type
- quantity
- metadata_json
- created_at

Possible usage types:

- embedding_tokens
- generation_tokens
- uploads
- search_requests

Indexes:

- organization_id
- usage_type
- created_at

---

# 5.11 audit_logs

Purpose:

- security auditing
- operational traceability

Important fields:

- id
- organization_id
- actor_user_id
- event_type
- metadata_json
- created_at

Indexes:

- organization_id
- event_type
- created_at

---

# 6. Entity Relationships

Important relationships:

- organizations → memberships
- users → memberships
- organizations → documents
- documents → processing_jobs
- documents → document_chunks
- organizations → api_keys
- organizations → query_logs
- query_logs → generated_answers

All tenant resources ultimately connect back to organizations.

---

# 7. Vector Database Design

# 7.1 Qdrant Collection Strategy

Recommended MVP strategy:

- single collection
- payload-based tenant filtering

Future scalability may introduce:

- per-tenant collections
- per-region collections

---

# 7.2 Vector Payload Structure

Each vector payload should contain at minimum:

- organization_id
- document_id
- chunk_id
- chunk_index
- filename
- page_number
- section
- embedding_model
- created_at

---

# 7.3 Embedding Versioning

Embedding metadata should track:

- embedding model
- embedding dimensions
- embedding version

This enables:

- reindexing
- migration
- provider switching

---

# 7.4 Retrieval Filtering

All retrieval operations must filter by:

- organization_id

Optional filters may include:

- document_id
- tags
- metadata fields

---

# 8. Object Storage Design

# 8.1 Storage Layout

Recommended logical path structure:

    organizations/{organization_id}/documents/{document_id}/

Examples of stored artifacts:

- original.pdf
- extracted.txt
- chunks.json
- preprocessing.json

---

# 8.2 Artifact Preservation

Preserve:

- original uploads
- extracted text
- processing artifacts

This supports:

- debugging
- audits
- reprocessing
- provider migration

---

# 8.3 Cleanup Philosophy

Deletion strategy should prefer:

- soft deletion first
- asynchronous cleanup later

Immediate destructive deletion is discouraged.

---

# 9. Indexing Strategy

## 9.1 PostgreSQL Indexing Philosophy

Indexes should optimize:

- tenant-scoped queries
- status lookups
- document retrieval
- job polling
- audit access

---

## 9.2 Compound Indexes

Recommended compound indexes include:

- organization_id + created_at
- organization_id + status
- organization_id + document_id

---

## 9.3 Full-Text Search

Traditional PostgreSQL full-text search is not part of the MVP retrieval strategy.

Primary retrieval uses:

- vector similarity search

---

# 10. Migration Strategy

## 10.1 Migration Tooling

Use:

- Alembic

for all schema evolution.

---

## 10.2 Migration Rules

Migrations must be:

- versioned
- reversible where practical
- reviewed
- tested in CI

---

## 10.3 Destructive Changes

Avoid destructive schema changes without:

- backups
- migration planning
- rollback consideration

---

# 11. Data Lifecycle

# 11.1 Upload Lifecycle

Document lifecycle:

- uploaded
- processed
- indexed
- queried
- archived/deleted

---

# 11.2 Reindexing

Documents must support:

- re-embedding
- re-chunking
- provider migration

without requiring re-upload.

---

# 11.3 Retention

Retention strategy should remain configurable.

Future support may include:

- retention policies
- tenant-specific retention windows
- compliance-driven deletion

---

# 12. Reliability & Recovery

## 12.1 Persistence Reliability

Critical transactional state should live in PostgreSQL.

Vector indexes must be rebuildable from stored artifacts.

---

## 12.2 Backup Strategy

Critical backup targets:

- PostgreSQL
- object storage

Qdrant can be reconstructed if required.

---

## 12.3 Recovery Philosophy

Recovery should prioritize:

- correctness
- tenant safety
- auditability

over raw recovery speed.

---

# 13. Security Considerations

## 13.1 Sensitive Data

Never store:

- plaintext API keys
- plaintext passwords
- secrets in logs

---

## 13.2 Encryption

Production environments should support:

- encrypted transport
- encrypted storage
- secret rotation

---

## 13.3 Auditability

Security-sensitive actions should be auditable.

Examples:

- API key creation
- API key revocation
- membership changes
- document deletion

---

# 14. Observability Metadata

Persistence operations should emit metadata useful for:

- tracing
- debugging
- auditing
- performance analysis

Recommended correlation identifiers:

- request_id
- trace_id
- tenant_id
- job_id

---

# 15. Scalability Philosophy

The persistence layer is designed to scale incrementally.

Initial strategy:

- vertically scalable PostgreSQL
- horizontally scalable workers
- scalable vector search through Qdrant

Avoid premature distributed complexity.

---

# 16. Design Invariants

The following are mandatory persistence invariants:

- every major resource belongs to an organization
- every vector must be tenant-filterable
- every async job must be traceable
- every document must be recoverable
- every vector index must be rebuildable
- every critical mutation must be auditable
- every production secret must remain hashed or encrypted

---

# 17. Summary

Aetheris uses a multi-storage persistence architecture combining PostgreSQL, Qdrant, and object storage. The design prioritizes tenant isolation, operational observability, rebuildability, auditability, and future SaaS scalability while remaining lean enough for disciplined MVP implementation.

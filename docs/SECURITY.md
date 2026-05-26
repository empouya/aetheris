# Aetheris Security

# 1. Purpose

This document defines the security posture, access model, secret handling rules, tenant isolation requirements, threat assumptions, and security-related operational constraints for Aetheris.

The goal is to keep the platform safe for enterprise document processing, multi-tenant usage, and future SaaS operation.

---

# 2. Security Philosophy

Aetheris follows a security-by-default approach.

Security priorities are:

- tenant isolation
- authentication integrity
- authorization correctness
- secret protection
- input validation
- rate limiting
- auditability
- secure observability
- recoverability after failure

Security is treated as a core platform requirement, not a late-stage hardening task.

---

# 3. Threat Model Assumptions

Aetheris assumes the following risks are realistic:

- unauthorized access attempts
- cross-tenant data leakage
- stolen API keys
- compromised user credentials
- malicious or malformed document uploads
- prompt injection through untrusted content
- accidental internal misuse
- over-permissive service access
- log leakage of sensitive information
- provider outages or malicious upstream behavior

The platform must remain safe under these conditions.

---

# 4. Authentication Model

## 4.1 User Authentication

Human users authenticate with:

- email/password credentials
- JWT access tokens
- rotating refresh tokens

Access tokens should be short-lived.

Refresh tokens must be revocable.

---

## 4.2 API Key Authentication

Programmatic access uses organization-scoped API keys.

API keys:

- belong to one organization
- are shown only once at creation
- are stored hashed
- are revocable
- are auditable
- are rate-limited

---

## 4.3 Session Security

Refresh sessions must be persisted so they can be revoked and audited.

Session behavior must support:

- rotation
- revocation
- expiry
- explicit logout

---

# 5. Authorization Model

## 5.1 Tenant Enforcement

Every request must be scoped to an organization.

No request may access data outside its tenant context.

This applies to:

- documents
- chunks
- jobs
- query logs
- usage data
- audit events
- API keys

---

## 5.2 Roles

Initial roles:

- owner
- admin
- member

Role responsibilities:

- owner: organization control
- admin: operational management
- member: standard usage

---

## 5.3 Internal Authorization

Internal services and workers must also verify tenant ownership.

Internal calls are not implicitly trusted.

---

# 6. Secret Management

## 6.1 Source Control Rules

Secrets must never be committed to Git.

This includes:

- database passwords
- JWT secrets
- API keys
- provider keys
- object storage credentials
- signing keys

---

## 6.2 Runtime Secret Handling

Secrets should be injected at runtime through environment variables or secure secret managers.

They must not appear in:

- logs
- stack traces
- generated documentation
- test snapshots
- screenshots

---

## 6.3 Production Secret Storage

Production secrets should use secure secret management systems such as cloud secret stores.

Secrets must be rotated when necessary.

---

# 7. Password and Key Handling

## 7.1 Password Hashing

User passwords must never be stored in plaintext.

Use a strong password hashing scheme appropriate for the implementation stack.

---

## 7.2 API Key Storage

API keys must be stored only as hashes.

Recommended metadata stored with each key:

- prefix
- name
- creator
- created_at
- last_used_at
- revoked_at
- expiry

The plaintext key must never be recoverable after creation.

---

# 8. Rate Limiting and Abuse Control

## 8.1 Rate Limiting Requirement

All public APIs must be rate limited.

Rate limiting should apply per:

- API key
- IP address
- endpoint class where appropriate

---

## 8.2 Baseline Limit

Recommended MVP baseline:

- 100 requests per minute per API key

Stricter limits may apply to:

- authentication endpoints
- upload endpoints
- expensive generation endpoints

---

## 8.3 Abuse Detection Philosophy

The system should detect and reduce:

- excessive retries
- brute-force authentication attempts
- upload flooding
- retrieval spam
- job queue flooding

---

# 9. Input Validation and Upload Security

## 9.1 File Validation

Every upload must validate:

- file type
- MIME type
- file extension
- file size
- basic structural validity

---

## 9.2 Supported Upload Types

Initial allowed formats:

- PDF
- TXT
- MD

All other formats are rejected in the MVP.

---

## 9.3 Malicious Content Handling

Uploaded files are untrusted.

The system must treat them as potential threats because they may contain:

- malformed structures
- embedded payloads
- prompt injection attempts
- unexpectedly large content
- parser edge cases

---

## 9.4 Size Limits

Document size limits must be enforced both at:

- the API layer
- the reverse proxy layer

---

# 10. Prompt Injection Awareness

Aetheris processes document content as untrusted input.

The generation layer must not blindly obey instructions found inside documents.

Security posture for RAG should include:

- separation of system instructions from retrieved content
- explicit context boundaries
- refusal to follow document-internal instructions
- preference for grounded answers only

---

# 11. Tenant Isolation Security

## 11.1 Application-Level Isolation

Aetheris uses application-level tenant isolation in the MVP.

Every data access must verify organization ownership.

---

## 11.2 Shared Infrastructure Safety

Even when storage is shared across tenants:

- query filters must always include organization scope
- vector payloads must include tenant metadata
- object storage paths must remain tenant-scoped
- job records must remain tenant-scoped

---

## 11.3 Cross-Tenant Access Testing

Cross-tenant access prevention is mandatory and must be covered by tests.

This is a security boundary, not a convenience feature.

---

# 12. Logging Security

## 12.1 Log Redaction

Logs must never include:

- plaintext passwords
- plaintext API keys
- secrets
- full sensitive document payloads
- tokens in full

---

## 12.2 Correlation Metadata

Logs may include:

- request_id
- trace_id
- tenant_id
- user_id
- job_id

These are acceptable for debugging and tracing.

---

## 12.3 Safe Error Reporting

Error responses must not reveal sensitive implementation details.

They should remain:

- structured
- consistent
- minimal
- useful

---

# 13. Encryption and Transport Security

## 13.1 Transport Security

Production traffic must use HTTPS only.

Plain HTTP is not acceptable externally.

---

## 13.2 Storage Security

Production deployments should use encryption at rest for:

- database storage
- object storage
- backups

---

# 14. Data Protection

## 14.1 Sensitive Data Assumption

Enterprise documents may contain confidential or regulated information.

The system must therefore assume that:

- documents can be sensitive
- metadata can be sensitive
- query text can be sensitive
- generated answers can be sensitive

---

## 14.2 Data Minimization

Store only what is necessary for:

- retrieval
- citations
- auditing
- debugging
- billing readiness

Avoid unnecessary duplication of sensitive content.

---

## 14.3 Retention Readiness

The architecture must support future retention policies, export requests, and deletion workflows.

---

# 15. Auditability

## 15.1 Audited Events

The platform should audit important actions such as:

- login events
- refresh events
- logout events
- API key creation
- API key revocation
- document upload
- document deletion
- organization membership changes
- query execution

---

## 15.2 Audit Integrity

Audit records should be treated as operationally important records.

They should be:

- tenant-scoped
- timestamped
- durable
- searchable
- protected from accidental tampering

---

# 16. Dependency and Supply Chain Security

## 16.1 Dependency Discipline

Dependencies should be:

- pinned
- reviewed
- updated deliberately
- scanned for known vulnerabilities

---

## 16.2 Container Security

Containers should:

- run as non-root where possible
- use minimal base images
- avoid unnecessary packages
- avoid embedded secrets

---

# 17. Provider Security

Aetheris may call external or local providers for embeddings and generation.

Provider calls should be designed with the assumption that:

- upstream services can fail
- upstream services can be slow
- upstream services can return malformed or partial outputs

Provider failures must not compromise tenant boundaries or secret safety.

---

# 18. Operational Security

## 18.1 Environment Separation

Development, test, staging, and production environments must remain isolated.

Shared secrets or shared databases across environments are not allowed.

---

## 18.2 Access Surface Minimization

The public attack surface should remain small.

The MVP should avoid unnecessary:

- admin panels
- debug endpoints
- operational GUIs
- hidden backdoors

---

## 18.3 Production Debugging

Production debugging should rely on:

- logs
- metrics
- traces
- safe diagnostics

not direct database edits or manual state corruption.

---

# 19. Incident Response Principles

Security incidents should be handled with:

- containment
- audit review
- credential revocation
- tenant impact assessment
- recovery and remediation
- regression test creation where applicable

---

# 20. Security Invariants

The following are mandatory:

- every tenant boundary is explicit
- every authentication artifact is revocable
- every secret is stored outside source control
- every API key is hashed at rest
- every request is rate limited
- every upload is validated
- every generated answer is grounded in retrieved context
- every security-sensitive action is auditable
- every production environment is HTTPS-only
- every cross-tenant access path is tested

---

# 21. Summary

Aetheris is designed to be secure enough for real enterprise data from the start. The platform uses strong tenant isolation, revocable authentication, strict secret handling, secure logging, upload validation, and auditability as core platform rules rather than optional hardening steps.

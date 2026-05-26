# ADR 001: Adopt a Modular Monolith Architecture

## Status
Accepted

## Date
2026-05-26

## Context

Aetheris is a headless, multi-tenant backend for document ingestion, semantic retrieval, and retrieval-augmented generation. The platform must support:

- asynchronous document processing
- semantic search
- grounded answer generation
- strong tenant isolation
- future SaaS monetization
- production-grade observability
- manageable solo or small-team development

The main architectural options considered were:

1. A traditional monolith
2. A modular monolith
3. A microservices architecture

The system also needs to remain practical for local development, CI, testing, and future deployment on AWS.

## Decision

Aetheris will use a **modular monolith** architecture with asynchronous workers.

The public API, business logic, persistence, and orchestration logic will live in a single codebase and be deployed as a single application surface, with background workers as a separate runtime process.

The codebase will be divided into domain-oriented modules with explicit boundaries. The application will not be split into microservices at the MVP stage.

## Rationale

### Why not a traditional monolith

A traditional monolith tends to become structurally flat over time. Without explicit module boundaries, business logic and infrastructure concerns mix together, making the codebase harder to understand, test, and evolve.

Aetheris needs stronger internal discipline than a plain monolith provides.

### Why not microservices

Microservices would introduce unnecessary complexity at this stage:

- more deployment units
- network communication overhead
- distributed failure modes
- service discovery concerns
- more complex local development
- more expensive observability and debugging
- more difficult transactional consistency

The current project does not require that level of operational complexity to achieve its goals.

### Why modular monolith

A modular monolith provides the best balance for Aetheris:

- clear separation of business domains
- low operational overhead
- easier local development
- easier testing
- easier CI/CD
- simpler observability
- easier refactoring
- future compatibility with service extraction if scale later justifies it

This design is also consistent with the project’s goal of being professional and scalable without prematurely distributing the system.

## Consequences

### Positive consequences

- A single repository can contain the entire system.
- Developers can run the stack locally with fewer moving parts.
- Shared data access and consistency are easier to reason about.
- Domain boundaries can be enforced in code without distributed complexity.
- Workers can be scaled independently while keeping the core app cohesive.
- Future microservice extraction remains possible because modules are already separated by responsibility.

### Negative consequences

- The codebase must be carefully structured to avoid becoming a “big ball of mud.”
- Discipline is required to preserve module boundaries.
- Careless imports and shared utilities can still create tight coupling if not controlled.
- Extremely large-scale independent scaling of individual domains would eventually require extraction or specialization.

## Architecture Rules

The following rules are mandatory:

1. Each domain must live in its own module or package.
2. Modules must expose explicit service interfaces.
3. Cross-module imports must be deliberate and minimal.
4. Business rules must not live in route handlers.
5. Persistence logic must not leak into API handlers.
6. Asynchronous workflows must be executed by background workers.
7. Shared code must remain genuinely shared and not become a dumping ground.
8. New functionality must be added to the correct domain module rather than a generic utility layer.

## Initial Module Boundaries

The initial modules are:

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

## Implementation Notes

- FastAPI will serve as the HTTP interface.
- PostgreSQL will store transactional data.
- Qdrant will store vector embeddings.
- Redis and Celery will handle background tasks.
- Object storage will hold uploaded files and derived artifacts.
- Nginx will act as reverse proxy in containerized deployments.

## Alternatives Considered

### Traditional monolith
Rejected because it lacks explicit structural discipline.

### Microservices
Rejected for the MVP because the operational and cognitive overhead is too high.

## Validation

This decision is valid if the system can satisfy the following:

- local development is easy and reproducible
- API services remain responsive
- worker processing is isolated from request handling
- code remains maintainable over time
- future scalability is preserved without early distribution

## Related Decisions

- API versioning and REST-first design
- PostgreSQL as primary transactional store
- Qdrant as vector database
- Redis and Celery for asynchronous processing
- OpenTelemetry-ready observability

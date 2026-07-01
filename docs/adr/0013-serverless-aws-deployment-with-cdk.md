# ADR-0013: Serverless AWS Deployment With CDK

Status: Accepted
Date: 2026-07-01

## Context

ADR-0012 established that the API and the web SPA deploy as separate artifacts
over CORS, and the runbook (`standards/deployment.md`) first described that with a
container/`docker compose` reference stack. We are now committing to a concrete
production target: **serverless on AWS, provisioned with the AWS CDK**.

Constraints that shape the decision:

- **A PostgreSQL RDS instance already exists** in the AWS account. Nexus must not
  provision its own database server — it consumes a **new database (and role)
  inside the pre-existing RDS instance**. The RDS instance is out of scope for this
  project's IaC; CDK only *references* it (VPC, subnets, security group).
- **Secrets must live in SSM Parameter Store and be read at runtime.** Secret
  values must never appear in plaintext in a Lambda definition, in environment
  variables, or in a CloudFormation template. Only SSM parameter **names** may be
  passed to the function; the application resolves the values at runtime.
- The API is a synchronous FastAPI app (Python 3.12) with no LLM in-process
  (ADR-0008); PostgreSQL is the only source of truth (ADR-0004). It fits a
  request/response serverless model well.

## Decision

1. **API on Lambda from the existing container image.** The API runs as an AWS
   Lambda **container-image** function built from the root `Dockerfile`, extended
   with the **AWS Lambda Web Adapter** so `uvicorn`/ASGI runs unmodified (no
   Mangum handler, no application code change). It is fronted by an **API Gateway
   HTTP API** (custom domain + throttling; a Lambda Function URL is the simpler
   fallback).
2. **Web SPA on S3 + CloudFront.** The Vite build is uploaded to a private **S3**
   bucket and served through **CloudFront** (Origin Access Control, SPA fallback
   so 403/404 → `index.html`). `VITE_API_URL` is inlined at build time and the
   image/bundle is rebuilt when it changes.
3. **Consume the pre-existing RDS.** CDK **references** the existing VPC and RDS
   security group; it does **not** create a database instance. A new logical
   **database and least-privilege role** are provisioned inside that instance for
   Nexus. The API Lambda runs **inside the VPC** (private subnets) and is allowed
   to reach RDS on 5432 via security-group rules.
4. **Secrets in SSM, resolved at runtime via an `ssm:` value convention.**
   `DATABASE_URL`, `NEXUS_TOKEN_SECRET`, and `NEXUS_OIDC_CLIENT_SECRET` are stored as
   **SSM `SecureString`** parameters. CDK sets the normal env var to a **pointer**
   whose value starts with `ssm:`, e.g.
   `NEXUS_TOKEN_SECRET=ssm:/nexus/prod/token-secret`, and grants the Lambda role
   `ssm:GetParameter` + `kms:Decrypt`. At runtime, `app/config.py` detects any env
   var value starting with `ssm:` and resolves (decrypts) the named parameter;
   `get_settings()` does this once per cold start and caches it. The convention is
   uniform — any env var may use an `ssm:` pointer — and non-secret config (public
   URLs, org slug, CORS origins) simply stays as plain values.
5. **Migrations as a discrete one-shot Lambda.** Alembic runs as a **separate
   Lambda built from the same image** with `CMD ["alembic","upgrade","head"]`,
   invoked once per deploy **before** shifting traffic — never at API cold start,
   so concurrent executions never race on schema changes.
6. **IaC in CDK (Python).** The infrastructure lives in `infra/` as a CDK app in
   **Python**, matching the backend so API and infra share one language and
   toolchain. Stacks are split by lifecycle: a networking/reference stack (VPC and
   RDS SG lookups), an API stack (Lambda, API Gateway, SSM grants), and a web stack
   (S3 + CloudFront).

## Consequences

- No servers, containers-at-rest, or `docker compose` in production. `docker
  compose` remains a **local development / integration** tool only; the reference
  `docker-compose.prod.yml` is demoted to a local prod-like harness, not the deploy
  path.
- The app gained a small **runtime SSM resolver** in `app/config.py`: when an env
  var value starts with `ssm:`, the remainder is resolved from SSM (`boto3`,
  `WithDecryption=True`) instead of used verbatim. Local dev keeps using plain env
  vars / `.env`, so the change is additive and backward compatible. `boto3` is a
  runtime dependency and is imported lazily (only when an `ssm:` value is present).
- **Lambda-in-VPC networking**: outbound access is required for the Google OIDC
  token exchange, so the private subnets need a **NAT Gateway** (or equivalent
  egress); AWS API calls (SSM, ECR image pull, CloudWatch Logs) use VPC endpoints
  or the same NAT. This is an operational cost to plan for.
- **Connection management**: many concurrent Lambdas can exhaust RDS connections.
  Mitigate with a small per-Lambda pool plus **RDS Proxy** and/or bounded reserved
  concurrency. This is the primary serverless-plus-RDS risk.
- Health endpoints (`/health`, `/health/live`, `/health/ready`) stay, but serve
  **deploy smoke tests and synthetic canaries** rather than orchestrator probes
  (there is no Kubernetes). TLS terminates at CloudFront and API Gateway (ACM), so
  no reverse proxy is needed.
- ADR-0012's "separate deployments over CORS" decision is unchanged; this ADR only
  fixes *how* each artifact is hosted.

## Alternatives Considered

| Alternative | Rejection reason |
| --- | --- |
| ECS Fargate behind an ALB | "Serverless" but does not scale to zero and adds always-on cost; the request/response API fits Lambda. Kept as a fallback if cold starts or VPC egress prove problematic. |
| Mangum ASGI handler | Requires a new handler and a `mangum` dependency in the app; the Lambda Web Adapter runs the existing `uvicorn` command with zero code change. |
| Aurora Serverless v2 (new cluster) | An RDS instance already exists; provisioning a second database server is wasteful. Consume the existing instance. |
| Secrets in Lambda env vars (even if from SSM at deploy time) | Puts secret values in the function definition and CloudFormation; violates the "no plaintext secrets in the Lambda def / env vars" constraint. Resolve at runtime instead. |
| Migrations at API startup | Multiple concurrent Lambda executions would race on schema changes; run migrations once as a separate step. |
| CDK in TypeScript | Aligns with the web stack, but Python matches the backend and keeps API + infra in one language; revisit if a TS backend migration ever happens. |

## Links

| Spec | File |
| --- | --- |
| Deployment runbook | `standards/deployment.md` |
| Separate deployments | `docs/adr/0012-web-client-and-separate-deployments.md` |
| Source of truth | `docs/adr/0004-postgresql-source-of-truth.md` |
| Auth/OIDC | `docs/adr/0010-oidc-short-lived-user-sessions.md` |

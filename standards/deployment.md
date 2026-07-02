# Production Deployment Runbook

This runbook covers deploying the Nexus API and web client to production on
**AWS, serverless, provisioned with the AWS CDK** (ADR-0013). It is the
operational contract for building artifacts, provisioning identity, handling
secrets, running migrations, and scaling. Behavior contracts live in `specs/`;
this document is concerned with how the system is operated.

Nexus deploys as two independently shipped artifacts (ADR-0012), now on serverless
AWS primitives:

- The **API** — FastAPI + SQLAlchemy, Python 3.12, synchronous — runs as an **AWS
  Lambda container-image function** (built from the root `Dockerfile` + the AWS
  Lambda Web Adapter) behind an **API Gateway HTTP API**.
- The **web SPA** — React + TanStack Router, built with Vite — is uploaded to
  **S3** and served by **CloudFront**.

PostgreSQL is the only source of truth (ADR-0004). It runs in a **pre-existing RDS
instance** in the account; Nexus consumes a **new database inside it** and does not
provision its own database server.

## Architecture

```
                    ┌───────────────┐        ┌──────────────────────┐
   Browser  ─────▶  │  CloudFront   │ ─────▶ │  S3 (private, OAC)    │  web SPA
                    └───────────────┘        └──────────────────────┘
                    ┌───────────────┐        ┌──────────────────────┐
   Clients  ─────▶  │  API Gateway  │ ─────▶ │  Lambda (API image)  │  FastAPI
   (CLI/web)        │   HTTP API    │        │  in VPC, Web Adapter │
                    └───────────────┘        └──────────┬───────────┘
                                                        │ 5432 (SG)
                       SSM Parameter Store (SecureString)│
                       resolved at runtime  ◀────────────┤
                                                        ▼
                                          ┌──────────────────────────┐
                                          │  Existing RDS PostgreSQL  │
                                          │  new "nexus" database     │
                                          └──────────────────────────┘
```

## Artifacts

| Artifact | Build context | Notes |
| --- | --- | --- |
| API image | `Dockerfile` (repo root) | Multi-stage, uv, non-root. Reused as a **Lambda container image**; the Lambda Web Adapter runs the existing `uvicorn` command unchanged. |
| Migrate task | Same image, command `alembic upgrade head` | One-shot **Fargate** task run as a discrete deploy step. |
| Web bundle | `web/` via `bun run build` | Static files uploaded to S3; `VITE_API_URL` inlined at build time. |
| Infrastructure | `infra/` (CDK, TypeScript) | Provisions everything below except the pre-existing RDS instance and VPC, which are referenced. |

The API image deliberately does **not** run migrations at startup. Migrations are a
separate step (see below) so concurrent Lambda executions never race on schema
changes.

## Secrets: SSM Parameter Store, resolved at runtime

**Hard rule (ADR-0013): secret values never appear in plaintext in a Lambda
definition, in an environment variable, or in a CloudFormation template.** Only an
SSM parameter **pointer** is passed to the function; the application resolves the
value at runtime.

Store these as SSM **`SecureString`** parameters (KMS-encrypted):

| Secret | Suggested parameter name |
| --- | --- |
| `DATABASE_URL` (contains the DB password) | `/nexus/prod/database-url` |
| `NEXUS_TOKEN_SECRET` | `/nexus/prod/token-secret` |
| `NEXUS_OIDC_CLIENT_SECRET` | `/nexus/prod/oidc-client-secret` |

The convention is simple: **any env var whose value starts with `ssm:` is a
pointer to an SSM parameter, resolved at runtime.** CDK sets the normal env var to
`ssm:<parameter-name>` and grants the Lambda execution role `ssm:GetParameter`
(+ `kms:Decrypt` for the CMK):

```
NEXUS_TOKEN_SECRET=ssm:/nexus/prod/token-secret
DATABASE_URL=ssm:/nexus/prod/database-url
NEXUS_OIDC_CLIENT_SECRET=ssm:/nexus/prod/oidc-client-secret
```

`app/config.py` resolves each `ssm:` value at runtime: it fetches the named
parameter from SSM (`boto3`, `WithDecryption=True`) and caches it for the execution
environment's lifetime (`get_settings()` is `lru_cache`d; `boto3` is imported
lazily, only when an `ssm:` value is present). Any env var set to a plain value
(local dev, `.env`) is used directly. This keeps local development unchanged while
production stores only pointers. The convention is uniform — non-secret vars may use
`ssm:` too — but secrets are the reason it exists.

Rotating `NEXUS_TOKEN_SECRET` invalidates outstanding access tokens, refresh
tokens, login codes, and OIDC state — rotate the SSM parameter deliberately and
recycle the function (new executions pick up the new value on cold start).

## Non-secret configuration (plain env vars)

Set on the API Lambda directly (no secret content):

| Variable | Purpose |
| --- | --- |
| `NEXUS_OIDC_CLIENT_ID` | Google OAuth client id (public). |
| `NEXUS_OIDC_ORG_SLUG` | Org that OIDC logins map to (default `acme`). |
| `NEXUS_PUBLIC_BASE_URL` | Public API base URL (the API Gateway custom domain). OIDC redirect and CLI links are built from it. |
| `NEXUS_WEB_BASE_URL` | Public SPA base URL (the CloudFront custom domain). |
| `NEXUS_WEB_LOGIN_REDIRECT_URIS` | Comma-separated allowlist of SPA callback URLs for OIDC. |
| `NEXUS_CORS_ORIGINS` | Comma-separated cross-origin allowlist for the web client. |
| `NEXUS_DEV_LOGIN` | **Must be unset/false.** Local-only password-less login. Never enable in production. |

Web build-time only:

| Variable | Purpose |
| --- | --- |
| `VITE_API_URL` | Public API base URL. **Inlined into the bundle at build time** — pass as a build arg; changing it requires rebuilding and re-uploading the SPA. |

## Consuming the existing RDS

The RDS instance already exists and is **not** managed by this CDK app. CDK looks
up the VPC and the RDS security group and wires connectivity; it does not create a
database server.

1. Create a dedicated database and least-privilege role inside the instance:

   ```sql
   CREATE ROLE nexus_app LOGIN PASSWORD '<generated>';
   CREATE DATABASE nexus OWNER nexus_app;
   -- Connect to the new database and grant schema privileges as needed.
   ```

2. Build the connection string and store it as the `DATABASE_URL` SecureString:

   ```
   postgresql+psycopg://nexus_app:<password>@<rds-endpoint>:5432/nexus
   ```

3. The API Lambda runs **inside the VPC** (private subnets). CDK adds a
   security-group rule allowing the Lambda SG to reach the RDS SG on 5432.

4. Because the Lambda is in the VPC, plan **outbound egress**: the Google OIDC
   token exchange needs internet access (NAT Gateway), and AWS API calls (SSM, ECR
   image pull, CloudWatch Logs) use VPC endpoints or the same NAT.

5. **Connection limits:** many concurrent Lambdas can exhaust RDS connections. Use
   a small per-Lambda SQLAlchemy pool plus **RDS Proxy** and/or bounded reserved
   concurrency on the API function.

## Google OIDC provisioning

Production web login uses Google OIDC. Provision it once per environment:

1. In the Google Cloud console, open **APIs & Services → Credentials**.
2. Configure the OAuth consent screen for the organization if not already done.
3. Create an **OAuth 2.0 Client ID** of type **Web application**.
4. Set **Authorized JavaScript origins** to the SPA origin (the CloudFront domain,
   i.e. `NEXUS_WEB_BASE_URL`), e.g. `https://app.example.com`.
5. Set the **Authorized redirect URI** to the API callback:
   `${NEXUS_PUBLIC_BASE_URL}/v1/auth/oidc/google/callback`
   (e.g. `https://api.example.com/v1/auth/oidc/google/callback`).
6. Store the credentials:
   - client id → `NEXUS_OIDC_CLIENT_ID` (plain env var, public).
   - client secret → `/nexus/prod/oidc-client-secret` (SSM SecureString).
7. Set `NEXUS_WEB_LOGIN_REDIRECT_URIS` to the SPA callback the API may redirect to:
   `${NEXUS_WEB_BASE_URL}/auth/callback`.

If `NEXUS_OIDC_CLIENT_ID` / the client-secret parameter are empty, OIDC is disabled
and the authorize endpoint returns 404 — do not deploy production without them.

## Migrations as a deploy step

Alembic reads `DATABASE_URL` via `app/config.py` (resolved from SSM at runtime), so
the migrate task needs only the `DATABASE_URL=ssm:...` pointer and the same SSM/KMS
grants and VPC placement as the API. It runs as a one-shot **Fargate** task that
reuses the API image with the command overridden to `alembic upgrade head`. Run it
exactly once per deploy, before the new API version serves traffic, and never from
the API entrypoint.

The API stack outputs the cluster, task family, subnets, and security group needed
to invoke it:

```sh
aws ecs run-task \
  --cluster "$MigrateClusterName" \
  --task-definition "$MigrateTaskFamily" \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$MigrateSubnetIds],securityGroups=[$MigrateSecurityGroupId],assignPublicIp=DISABLED}"
```

Migrations are additive and reviewed per `standards/database-migrations.md`. With
concurrent API executions, run the single migration step first, then shift traffic.

## Bootstrap the first organization and admin

The admin API requires an existing org admin, and OIDC login rejects unknown
emails — so a fresh database cannot onboard anyone through the API. Break the
cycle once per organization with `scripts/bootstrap_org.py`, run as a discrete
one-shot Fargate task that reuses the API image and `DATABASE_URL` (the same
placement and SSM/KMS grants as the migrate task), after migrations have run:

```sh
uv run python -m scripts.bootstrap_org \
  --org-slug acme --org-name "Acme" \
  --admin-email admin@acme.example --admin-name "Acme Admin"
```

It creates the organization plus one active user with `is_org_admin = true`
(knowledge role `knowledge_admin` by default; override with `--role`). It is
idempotent: an existing org/user is reused, the user is reactivated, and the
org-admin membership is ensured — so it is safe to re-run, including to recover
from an admin lockout. `--admin-email` must match the identity the admin signs in
with (their Google account in production). After bootstrap, that admin adds and
manages everyone else through the admin API or the web app; this command is not
part of onboarding additional people.

## Provisioning with CDK

Infrastructure lives in `infra/` as a **CDK app in TypeScript** (see
`infra/README.md`), split into two independent stacks with no cross-stack
references:

| Stack | Owns | References |
| --- | --- | --- |
| `Nexus-Api-<env>` | Lambda (container image), API Gateway HTTP API, migrate Fargate task, SG rules, SSM/KMS grants | Existing VPC, existing RDS SG, SSM params |
| `Nexus-Web-<env>` | S3 bucket, CloudFront distribution (OAC), optional ACM cert/domain | — |

```sh
cd infra
bun install
bun run build                        # tsc type-check
bunx cdk diff                        # review the change set
bunx cdk deploy --all                # or deploy one stack at a time
```

Per-environment values live in `infra/cdk.json` under `context.environments.<env>`;
select one with `-c env=<name>`. Secrets are created out-of-band (see above) and
only **referenced** by their SSM parameter name — never passed as values.

## Health and readiness

The API exposes three endpoints (`app/main.py`):

| Endpoint | Meaning | Use |
| --- | --- | --- |
| `GET /health` | Process is up; returns service/version/time. | Basic ping. |
| `GET /health/live` | Liveness. | Synthetic canary. |
| `GET /health/ready` | Readiness — verifies DB connectivity. | Deploy smoke test; returns 503 when the DB is unreachable. |

On Lambda there is no orchestrator liveness/readiness probe; use `/health/ready` as
a **post-deploy smoke test** and (optionally) a CloudWatch Synthetics canary.

## Scaling and connections

The API is stateless and safe to run at high concurrency:

- Sessions are JWT access tokens plus DB-backed refresh/auth sessions; there is no
  in-process session state.
- All persistent state lives in PostgreSQL, shared by every execution.
- Lambda scales concurrency automatically. **Guard the database**: use RDS Proxy
  and/or reserved concurrency so a concurrency spike cannot exhaust RDS connections.
- Run the migration step **once** per deploy (not per execution).

## Backup and restore

PostgreSQL is the single source of truth; back it up accordingly.

- Use the existing RDS instance's automated backups / snapshots and enable
  point-in-time recovery. The Nexus database is one database inside that instance.
- For portable restores, take logical backups of the `nexus` database
  (`pg_dump`) in addition to instance snapshots.
- There are no derived indexes to rebuild in v1.
- Store backups encrypted and test restores periodically.

## TLS and domains

- TLS terminates at **CloudFront** (web) and **API Gateway** (API) with ACM
  certificates; there is no reverse proxy to manage.
- `NEXUS_PUBLIC_BASE_URL` and `NEXUS_WEB_BASE_URL` must be the public `https://`
  custom-domain URLs — OIDC redirect URIs and CLI links are built from them and
  must match what Google and browsers see.
- API Gateway preserves/echoes `X-Request-Id` for tracing; keep it end to end.
- RDS stays private (no public accessibility); only the API Lambda SG may reach it.

## Deploy checklist

1. Build and push the API container image to ECR; build and upload the web bundle
   to S3 (web needs `VITE_API_URL` at build time).
2. Ensure the SSM `SecureString` parameters exist and the Lambda role has
   `ssm:GetParameter` + `kms:Decrypt`. **No secret values in env vars or CDK.**
3. Confirm `NEXUS_DEV_LOGIN` is unset.
4. `bunx cdk deploy --all` from `infra/` (review `bunx cdk diff` first).
5. Run the migrate Fargate task (`alembic upgrade head`) as a discrete step.
6. For a brand-new deployment only, bootstrap the first org and admin
   (`scripts.bootstrap_org`) as a one-shot task — see
   [Bootstrap the first organization and admin](#bootstrap-the-first-organization-and-admin).
7. Shift the API alias to the new version; verify `/health/ready` returns 200.
8. Invalidate the CloudFront cache if the SPA changed.
9. Smoke-test OIDC login through the SPA.

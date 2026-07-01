# Nexus Infrastructure (AWS CDK, TypeScript)

Serverless AWS infrastructure for Nexus (ADR-0013), as two independent stacks:

| Stack | Contents | Depends on |
| --- | --- | --- |
| `Nexus-Api-<env>` | API on **Lambda** (container image + AWS Lambda Web Adapter) behind an **API Gateway HTTP API**; a one-shot **Fargate** migrate task. Runs in the existing VPC and reaches the existing RDS. | Existing VPC + RDS (referenced, not created). |
| `Nexus-Web-<env>` | SPA on **S3** served by **CloudFront** (private bucket, OAC, SPA fallback). | Nothing — fully independent. |

The two stacks are deliberately separate (ADR-0012): different lifecycles and
failure domains, no cross-stack references. Deploy or roll back either alone.

## Prerequisites

- Node.js 20+ and `npm`, Docker (for building the API image asset), and AWS
  credentials for the target account.
- A **pre-existing RDS PostgreSQL** instance with a **`nexus` database + role**
  already created (see `standards/deployment.md`), and its VPC + security-group ids.
- The runtime secrets stored as **SSM `SecureString`** parameters (see below).
- The SPA built into `web/dist` before deploying the web stack.

## Configure

Edit `cdk.json` → `context.environments.<env>` (a `prod` template is included).
Select an environment at deploy time with `-c env=<name>` (default `prod`).

| Key | Meaning |
| --- | --- |
| `account`, `region` | Target AWS account and region. |
| `vpcId`, `rdsSecurityGroupId`, `dbPort` | Existing VPC/RDS to consume. |
| `manageRdsIngress` | If `true`, CDK adds ingress rules to the referenced RDS SG. |
| `ssm.databaseUrl` / `tokenSecret` / `oidcClientSecret` | **Names** of the SSM SecureString parameters (not values). |
| `ssm.kmsKeyArn` | KMS key encrypting the SecureStrings (omit/empty for the default `aws/ssm` key). |
| `oidcClientId`, `oidcOrgSlug` | Google OIDC (public) client id and org slug. |
| `publicBaseUrl`, `webBaseUrl` | Public API and SPA URLs. |
| `webLoginRedirectUris`, `corsOrigins` | Comma-separated allowlists. |
| `api`, `web` (optional) | `{ domainName, certificateArn }` for custom domains. |

**Secrets are never passed as values.** CDK sets each secret env var to a
pointer, e.g. `NEXUS_TOKEN_SECRET=ssm:/nexus/prod/token-secret`, and grants the
Lambda/task role `ssm:GetParameter` (+ `kms:Decrypt`). The app resolves it at
runtime (see `app/config.py`).

## Commands

```sh
npm install
npm run build          # tsc type-check
npx cdk diff           # review changes (needs AWS creds; the API stack looks up the VPC)
npx cdk deploy --all   # deploy both stacks

# Deploy one at a time:
npx cdk deploy Nexus-Api-prod
npx cdk deploy Nexus-Web-prod
```

Bootstrap the account/region once if you never have: `npx cdk bootstrap
aws://<account>/<region>`.

## Deploy order & migrations

1. Build and push the API image and deploy `Nexus-Api-<env>`.
2. **Run migrations** (discrete step) using the Fargate task the API stack
   created — the stack outputs everything you need:

   ```sh
   aws ecs run-task \
     --cluster "$(<MigrateClusterName output>)" \
     --task-definition "$(<MigrateTaskFamily output>)" \
     --launch-type FARGATE \
     --network-configuration "awsvpcConfiguration={subnets=[<MigrateSubnetIds>],securityGroups=[<MigrateSecurityGroupId>],assignPublicIp=DISABLED}"
   ```

3. Build the SPA and deploy the web stack:

   ```sh
   (cd ../web && VITE_API_URL=https://api.nexus.example.com bun run build)
   npx cdk deploy Nexus-Web-prod
   ```

   The web stack skips the bucket deployment (with a warning) if `web/dist` is
   missing, so `cdk synth`/`diff` stay green before a build.

See `standards/deployment.md` for the full runbook (OIDC provisioning, VPC egress,
RDS connections, TLS, backups).

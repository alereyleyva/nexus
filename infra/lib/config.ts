import type { App } from "aws-cdk-lib";

/**
 * Optional custom domain for an artifact (API Gateway or CloudFront).
 * `certificateArn` must be an ACM cert valid for `domainName` (CloudFront certs
 * must be in us-east-1).
 */
export interface DomainConfig {
  readonly domainName: string;
  readonly certificateArn: string;
  readonly hostedZoneId?: string;
  readonly hostedZoneName?: string;
}

/**
 * SSM SecureString parameter names holding the runtime secrets. The app resolves
 * any env var whose value starts with `ssm:` at runtime (see app/config.py), so
 * CDK only ever passes the parameter names — never the secret values.
 */
export interface SsmConfig {
  readonly databaseUrl: string;
  readonly tokenSecret: string;
  readonly oidcClientSecret: string;
  /** KMS key ARN used to encrypt the SecureStrings. Omit for the default aws/ssm key. */
  readonly kmsKeyArn?: string;
}

export interface NexusConfig {
  readonly envName: string;
  readonly account: string;
  readonly region: string;

  /** Pre-existing VPC the API/migrate run inside (looked up, not created). */
  readonly vpcId: string;
  /** Pre-existing RDS security group; the API is granted ingress to it on `dbPort`. */
  readonly rdsSecurityGroupId: string;
  readonly dbPort: number;
  /** When true, CDK adds ingress rules to the referenced RDS SG. Disable to manage them out-of-band. */
  readonly manageRdsIngress: boolean;

  readonly ssm: SsmConfig;
  readonly oidcClientId: string;
  readonly oidcOrgSlug: string;
  readonly publicBaseUrl: string;
  readonly webBaseUrl: string;
  readonly webLoginRedirectUris: string;
  readonly corsOrigins: string;

  readonly api?: DomainConfig;
  readonly web?: DomainConfig;
}

function requireString(source: Record<string, unknown>, key: string, ctx: string): string {
  const value = source[key];
  if (typeof value !== "string" || value.length === 0) {
    throw new Error(
      `Missing required config '${ctx}.${key}'. Set it in infra/cdk.json ` +
        `under context.environments.<env>, or pass -c.`,
    );
  }
  return value;
}

function optionalDomain(value: unknown, ctx: string): DomainConfig | undefined {
  if (value === undefined) return undefined;
  const source = value as Record<string, unknown>;
  return {
    domainName: requireString(source, "domainName", ctx),
    certificateArn: requireString(source, "certificateArn", ctx),
    hostedZoneId: typeof source.hostedZoneId === "string" ? source.hostedZoneId : undefined,
    hostedZoneName: typeof source.hostedZoneName === "string" ? source.hostedZoneName : undefined,
  };
}

/**
 * Load the environment config from CDK context. Select the environment with
 * `-c env=<name>` (default `prod`); values live in cdk.json under
 * `context.environments.<name>`.
 */
export function getConfig(app: App): NexusConfig {
  const envName = (app.node.tryGetContext("env") as string | undefined) ?? "prod";
  const environments = (app.node.tryGetContext("environments") ?? {}) as Record<string, unknown>;
  const raw = environments[envName] as Record<string, unknown> | undefined;
  if (raw === undefined) {
    throw new Error(
      `Unknown environment '${envName}'. Define it in infra/cdk.json ` +
        `context.environments, or pass -c env=<name>.`,
    );
  }

  const ctx = `environments.${envName}`;
  const ssm = (raw.ssm ?? {}) as Record<string, unknown>;
  const dbPort = typeof raw.dbPort === "number" ? raw.dbPort : 5432;
  const manageRdsIngress = raw.manageRdsIngress !== false; // default true

  return {
    envName,
    account: requireString(raw, "account", ctx),
    region: requireString(raw, "region", ctx),
    vpcId: requireString(raw, "vpcId", ctx),
    rdsSecurityGroupId: requireString(raw, "rdsSecurityGroupId", ctx),
    dbPort,
    manageRdsIngress,
    ssm: {
      databaseUrl: requireString(ssm, "databaseUrl", `${ctx}.ssm`),
      tokenSecret: requireString(ssm, "tokenSecret", `${ctx}.ssm`),
      oidcClientSecret: requireString(ssm, "oidcClientSecret", `${ctx}.ssm`),
      kmsKeyArn: typeof ssm.kmsKeyArn === "string" ? ssm.kmsKeyArn : undefined,
    },
    oidcClientId: requireString(raw, "oidcClientId", ctx),
    oidcOrgSlug: typeof raw.oidcOrgSlug === "string" ? raw.oidcOrgSlug : "aircury",
    publicBaseUrl: requireString(raw, "publicBaseUrl", ctx),
    webBaseUrl: requireString(raw, "webBaseUrl", ctx),
    webLoginRedirectUris: requireString(raw, "webLoginRedirectUris", ctx),
    corsOrigins: requireString(raw, "corsOrigins", ctx),
    api: optionalDomain(raw.api, `${ctx}.api`),
    web: optionalDomain(raw.web, `${ctx}.web`),
  };
}

/**
 * The runtime environment shared by the API Lambda and the migrate task. Secret
 * values are passed as `ssm:<name>` pointers, resolved at runtime by the app.
 * NEXUS_DEV_LOGIN is intentionally absent (dev-login must be off in production).
 */
export function appEnvironment(config: NexusConfig): Record<string, string> {
  return {
    DATABASE_URL: `ssm:${config.ssm.databaseUrl}`,
    NEXUS_TOKEN_SECRET: `ssm:${config.ssm.tokenSecret}`,
    NEXUS_OIDC_CLIENT_SECRET: `ssm:${config.ssm.oidcClientSecret}`,
    NEXUS_OIDC_CLIENT_ID: config.oidcClientId,
    NEXUS_OIDC_ORG_SLUG: config.oidcOrgSlug,
    NEXUS_PUBLIC_BASE_URL: config.publicBaseUrl,
    NEXUS_WEB_BASE_URL: config.webBaseUrl,
    NEXUS_WEB_LOGIN_REDIRECT_URIS: config.webLoginRedirectUris,
    NEXUS_CORS_ORIGINS: config.corsOrigins,
  };
}

/** ARNs of the SSM parameters the app resolves at runtime (for IAM grants). */
export function ssmParameterArns(config: NexusConfig): string[] {
  const arn = (name: string): string => {
    const path = name.startsWith("/") ? name : `/${name}`;
    return `arn:aws:ssm:${config.region}:${config.account}:parameter${path}`;
  };
  return [config.ssm.databaseUrl, config.ssm.tokenSecret, config.ssm.oidcClientSecret].map(arn);
}

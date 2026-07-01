import * as path from "node:path";
import * as cdk from "aws-cdk-lib";
import * as apigwv2 from "aws-cdk-lib/aws-apigatewayv2";
import { HttpLambdaIntegration } from "aws-cdk-lib/aws-apigatewayv2-integrations";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as iam from "aws-cdk-lib/aws-iam";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as logs from "aws-cdk-lib/aws-logs";
import type { Construct } from "constructs";
import { appEnvironment, type NexusConfig, ssmParameterArns } from "./config";

const REPO_ROOT = path.resolve(__dirname, "..", "..");

export interface NexusApiStackProps extends cdk.StackProps {
  readonly config: NexusConfig;
}

/**
 * API stack: the FastAPI app on Lambda (container image + AWS Lambda Web Adapter)
 * behind an API Gateway HTTP API, plus a one-shot Fargate task that runs Alembic
 * migrations. Runs inside the pre-existing VPC and reaches the pre-existing RDS.
 */
export class NexusApiStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: NexusApiStackProps) {
    super(scope, id, props);
    const { config } = props;

    const vpc = ec2.Vpc.fromLookup(this, "Vpc", { vpcId: config.vpcId });
    const subnets = vpc.selectSubnets({ subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS });

    const rdsSg = ec2.SecurityGroup.fromSecurityGroupId(
      this,
      "RdsSg",
      config.rdsSecurityGroupId,
      { mutable: config.manageRdsIngress },
    );

    const ssmArns = ssmParameterArns(config);
    const grantSecretsRead = (grantee: iam.IGrantable): void => {
      grantee.grantPrincipal.addToPrincipalPolicy(
        new iam.PolicyStatement({
          actions: ["ssm:GetParameter", "ssm:GetParameters"],
          resources: ssmArns,
        }),
      );
      if (config.ssm.kmsKeyArn) {
        grantee.grantPrincipal.addToPrincipalPolicy(
          new iam.PolicyStatement({ actions: ["kms:Decrypt"], resources: [config.ssm.kmsKeyArn] }),
        );
      }
    };

    // --- API Lambda (container image) --------------------------------------
    const apiSg = new ec2.SecurityGroup(this, "ApiSg", {
      vpc,
      description: "Nexus API Lambda",
      allowAllOutbound: true,
    });
    if (config.manageRdsIngress) {
      rdsSg.addIngressRule(apiSg, ec2.Port.tcp(config.dbPort), "Nexus API to RDS");
    }

    const apiFn = new lambda.DockerImageFunction(this, "ApiFn", {
      code: lambda.DockerImageCode.fromImageAsset(REPO_ROOT, {
        file: "Dockerfile",
        // One uvicorn worker per Lambda execution environment; Lambda handles concurrency.
        cmd: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"],
      }),
      architecture: lambda.Architecture.X86_64,
      memorySize: 1024,
      timeout: cdk.Duration.seconds(30),
      vpc,
      vpcSubnets: subnets,
      securityGroups: [apiSg],
      environment: appEnvironment(config),
      logRetention: logs.RetentionDays.ONE_MONTH,
    });
    grantSecretsRead(apiFn);

    const httpApi = new apigwv2.HttpApi(this, "HttpApi", {
      defaultIntegration: new HttpLambdaIntegration("ApiIntegration", apiFn),
    });

    if (config.api) {
      const domain = new apigwv2.DomainName(this, "ApiDomain", {
        domainName: config.api.domainName,
        certificate: cdk.aws_certificatemanager.Certificate.fromCertificateArn(
          this,
          "ApiCert",
          config.api.certificateArn,
        ),
      });
      new apigwv2.ApiMapping(this, "ApiMapping", { api: httpApi, domainName: domain });
    }

    // --- One-shot migrate task (Fargate) -----------------------------------
    // Reuses the same image; overrides the command to run migrations once. Invoke
    // it as a discrete deploy step with `aws ecs run-task` (see infra/README.md).
    const cluster = new ecs.Cluster(this, "MigrateCluster", { vpc });
    const migrateSg = new ec2.SecurityGroup(this, "MigrateSg", {
      vpc,
      description: "Nexus migrate task",
      allowAllOutbound: true,
    });
    if (config.manageRdsIngress) {
      rdsSg.addIngressRule(migrateSg, ec2.Port.tcp(config.dbPort), "Nexus migrate to RDS");
    }

    const migrateTask = new ecs.FargateTaskDefinition(this, "MigrateTask", {
      cpu: 256,
      memoryLimitMiB: 512,
    });
    migrateTask.addContainer("migrate", {
      image: ecs.ContainerImage.fromAsset(REPO_ROOT, { file: "Dockerfile" }),
      command: ["alembic", "upgrade", "head"],
      environment: appEnvironment(config),
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: "nexus-migrate",
        logRetention: logs.RetentionDays.ONE_MONTH,
      }),
    });
    grantSecretsRead(migrateTask.taskRole);

    // --- Outputs -----------------------------------------------------------
    new cdk.CfnOutput(this, "ApiUrl", { value: httpApi.apiEndpoint });
    new cdk.CfnOutput(this, "MigrateClusterName", { value: cluster.clusterName });
    new cdk.CfnOutput(this, "MigrateTaskFamily", { value: migrateTask.family });
    new cdk.CfnOutput(this, "MigrateSubnetIds", { value: subnets.subnetIds.join(",") });
    new cdk.CfnOutput(this, "MigrateSecurityGroupId", { value: migrateSg.securityGroupId });
  }
}

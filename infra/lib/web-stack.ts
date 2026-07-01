import * as fs from "node:fs";
import * as path from "node:path";
import * as cdk from "aws-cdk-lib";
import * as cloudfront from "aws-cdk-lib/aws-cloudfront";
import * as origins from "aws-cdk-lib/aws-cloudfront-origins";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as s3deploy from "aws-cdk-lib/aws-s3-deployment";
import type { Construct } from "constructs";
import type { NexusConfig } from "./config";

const WEB_DIST = path.resolve(__dirname, "..", "..", "web", "dist");

export interface NexusWebStackProps extends cdk.StackProps {
  readonly config: NexusConfig;
}

/**
 * Web stack: the built SPA in a private S3 bucket served by CloudFront with SPA
 * history fallback. Fully independent of the API stack (no VPC, no RDS). Build
 * the SPA first (`VITE_API_URL=<api-url> bun run build` in web/) so web/dist
 * exists; the bucket deployment is skipped when it does not, keeping synth green.
 */
export class NexusWebStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: NexusWebStackProps) {
    super(scope, id, props);
    const { config } = props;

    const bucket = new s3.Bucket(this, "WebBucket", {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    const spaFallback: cloudfront.ErrorResponse[] = [403, 404].map((httpStatus) => ({
      httpStatus,
      responseHttpStatus: 200,
      responsePagePath: "/index.html",
      ttl: cdk.Duration.minutes(5),
    }));

    const distribution = new cloudfront.Distribution(this, "WebDistribution", {
      defaultBehavior: {
        origin: origins.S3BucketOrigin.withOriginAccessControl(bucket),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
      },
      defaultRootObject: "index.html",
      errorResponses: spaFallback,
      priceClass: cloudfront.PriceClass.PRICE_CLASS_100,
      ...(config.web
        ? {
            domainNames: [config.web.domainName],
            certificate: cdk.aws_certificatemanager.Certificate.fromCertificateArn(
              this,
              "WebCert",
              config.web.certificateArn,
            ),
          }
        : {}),
    });

    if (fs.existsSync(WEB_DIST)) {
      new s3deploy.BucketDeployment(this, "DeployWeb", {
        sources: [s3deploy.Source.asset(WEB_DIST)],
        destinationBucket: bucket,
        distribution,
        distributionPaths: ["/*"],
      });
    } else {
      cdk.Annotations.of(this).addWarning(
        `web/dist not found — build the SPA before deploy: ` +
          `VITE_API_URL=${config.publicBaseUrl} bun run build (in web/).`,
      );
    }

    new cdk.CfnOutput(this, "WebBucketName", { value: bucket.bucketName });
    new cdk.CfnOutput(this, "DistributionId", { value: distribution.distributionId });
    new cdk.CfnOutput(this, "DistributionDomain", { value: distribution.distributionDomainName });
  }
}

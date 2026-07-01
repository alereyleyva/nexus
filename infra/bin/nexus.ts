#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { NexusApiStack } from "../lib/api-stack";
import { getConfig } from "../lib/config";
import { NexusWebStack } from "../lib/web-stack";

const app = new cdk.App();
const config = getConfig(app);
const env: cdk.Environment = { account: config.account, region: config.region };
const tags = { Project: "nexus", Environment: config.envName };

// The API and the web SPA deploy as separate, independent stacks (ADR-0012):
// different lifecycles, resources, and failure domains, no cross-stack references.
new NexusApiStack(app, `Nexus-Api-${config.envName}`, { env, config, tags });
new NexusWebStack(app, `Nexus-Web-${config.envName}`, { env, config, tags });

app.synth();

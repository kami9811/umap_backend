#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { CdkStack } from '../lib/cdk-stack';

const app: cdk.App = new cdk.App();

const getAppEnvironment = (): any => {
  // Get environment context
  const argContext: string = 'environment';
  const envKey: any = app.node.tryGetContext(argContext);
  if (envKey == undefined)
    throw new Error(`Please specify environment with context option. ex) cdk deploy -c ${argContext}=dev`);
  const envVals = app.node.tryGetContext(envKey);
  if (envVals == undefined) throw new Error('Invalid environment.');
  const env = {
    amplifyRepositoryUrl: envVals['env']['amplifyRepositoryUrl'],
    amplifyOauthToken: envVals['env']['amplifyOauthToken'],
    amplifyBranch: envVals['env']['amplifyBranch'],
    region: envVals['env']['region'],
  };
  return env;
};

new CdkStack(app, 'CdkStack', {
  /* If you don't specify 'env', this stack will be environment-agnostic.
   * Account/Region-dependent features and context lookups will not work,
   * but a single synthesized template can be deployed anywhere. */

  /* Uncomment the next line to specialize this stack for the AWS Account
   * and Region that are implied by the current CLI configuration. */
  // env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },

  /* Uncomment the next line if you know exactly what Account and Region you
   * want to deploy the stack to. */
  // env: { account: '123456789012', region: 'us-east-1' },

  /* For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html */
  env: getAppEnvironment(),
});
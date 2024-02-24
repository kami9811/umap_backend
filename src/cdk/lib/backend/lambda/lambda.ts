import { Duration } from "aws-cdk-lib/core";
import { Construct } from "constructs";
import { 
  LayerVersion,
  Code,
  DockerImageCode,
  Runtime,
  Function,
  DockerImageFunction,
} from "aws-cdk-lib/aws-lambda";
import {
  Vpc,
  SecurityGroup,
} from "aws-cdk-lib/aws-ec2";
import { ServerlessCluster } from "aws-cdk-lib/aws-rds";
import { PolicyStatement } from "aws-cdk-lib/aws-iam";
import {
  AwsCustomResource,
  AwsCustomResourcePolicy,
  PhysicalResourceId,
} from 'aws-cdk-lib/custom-resources';
import { Table } from "aws-cdk-lib/aws-dynamodb";


export function createDBProcessLayer(
  scope: Construct,
  id: string,
): LayerVersion {
  return new LayerVersion(scope, id, {
    code: Code.fromAsset('lib/backend/lambda/python/db_process_lambda_layer.zip'),
    compatibleRuntimes: [Runtime.PYTHON_3_12],
    description: 'A layer containing pymysql',
  });
}

export function createDataProcessLambdaLayer(
  scope: Construct,
  id: string,
): LayerVersion {
  return new LayerVersion(scope, id, {
    code: Code.fromAsset('lib/backend/lambda/python/data_process_lambda_layer.zip'),
    compatibleRuntimes: [Runtime.PYTHON_3_12],
    description: 'A layer containing onnxruntime, pandas, and numpy',
  });
}

export function createAuroraSetupLambda(
  scope: Construct,
  id: string,
  dbProcessLayer: LayerVersion,
  vpc: Vpc,
  lambdaSecurityGroup: SecurityGroup,
  cluster: ServerlessCluster,
  defaultDatabaseName: string,
): Function {
  return new Function(scope, id, {
    runtime: Runtime.PYTHON_3_12,
    handler: 'bootstrap-function.handler',
    code: Code.fromAsset('lib/backend/lambda/python/resources/auroradb'),
    layers: [dbProcessLayer],
    vpc: vpc,
    securityGroups: [lambdaSecurityGroup],
    environment: {
      SECRET_ARN: cluster.secret?.secretArn as string,
      DB_HOST: cluster.clusterEndpoint.hostname,
      DB_NAME: defaultDatabaseName,
    },
    timeout: Duration.seconds(600),
  });
}

export function addSecretsManagerPolicy(
  lambda: Function,
  cluster: ServerlessCluster,
): void {
  lambda.addToRolePolicy(new PolicyStatement({
    actions: ['rds-data:*', 'secretsmanager:GetSecretValue'],
    resources: ['*', cluster.secret?.secretArn || ''],
  }));
}

export function createAuroraDbSetupResource(
  scope: Construct,
  id: string,
  auroraSetupLambda: Function,
): AwsCustomResource {
  return new AwsCustomResource(scope, id, {
    onCreate: {
      service: 'Lambda',
      action: 'invoke',
      parameters: {
        FunctionName: auroraSetupLambda.functionName,
      },
      physicalResourceId: PhysicalResourceId.of(Date.now().toString()),
    },
    policy: AwsCustomResourcePolicy.fromStatements([
      new PolicyStatement({
        actions: ['lambda:InvokeFunction'],
        resources: [auroraSetupLambda.functionArn],
      })
    ]),
  });
}

export function createDBAccessLambdaFunction(
  scope: Construct,
  id: string,
  handler: string,
  code: Code,
  environment: { [key: string]: any },  // TODO: anyを避ける方法を検討
  cluster: ServerlessCluster,
  dynamoDBTable: Table,
  timeout: Duration = Duration.seconds(60),
): Function {
  const lambdaFunction: Function = new Function(scope, id, {
    runtime: Runtime.PYTHON_3_12,
    handler: handler,
    code: code,
    environment: environment,
    initialPolicy: [
      new PolicyStatement({
        actions: ['secretsmanager:GetSecretValue'],
        resources: [cluster.secret?.secretArn || ''],
      }),
    ],
    timeout: timeout,
  });

  // LambdaにDynamoDBとAuroraへのアクセス権を付与
  dynamoDBTable.grantReadWriteData(lambdaFunction);
  cluster.grantDataApiAccess(lambdaFunction);

  return lambdaFunction;
}

export function createDataProcessDBAccessLambdaFunction(
  scope: Construct,
  id: string,
  code: DockerImageCode,
  environment: { [key: string]: any },  // TODO: anyを避ける方法を検討
  cluster: ServerlessCluster,
  dynamoDBTable: Table,
  timeout: Duration = Duration.seconds(60),
  memorySize: number = 128,
): Function {
  const lambdaFunction: Function = new DockerImageFunction(scope, id, {
    code: code,
    environment: environment,
    initialPolicy: [
      new PolicyStatement({
        actions: ['secretsmanager:GetSecretValue'],
        resources: [cluster.secret?.secretArn || ''],
      }),
    ],
    timeout: timeout,
    memorySize: memorySize,
  });

  // LambdaにDynamoDBとAuroraへのアクセス権を付与
  dynamoDBTable.grantReadWriteData(lambdaFunction);
  cluster.grantDataApiAccess(lambdaFunction);

  return lambdaFunction;
}

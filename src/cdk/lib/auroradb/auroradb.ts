import { Construct } from 'constructs'
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { PythonLayerVersion } from 'aws-cdk-lib/aws-lambda-python';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { ServerlessCluster } from 'aws-cdk-lib/aws-rds';

class Auroradb extends Construct {
  constructor(scope: Construct, id: string) {
    super(scope, id);

    // VPCの設定（Aurora Serverless v2では必要です）
    const vpc = new ec2.Vpc(this, 'MyVpc');

    // Aurora Serverless v2のクラスター設定
    const cluster = new rds.ServerlessCluster(this, 'MyAuroraCluster', {
      engine: rds.DatabaseClusterEngine.AURORA_MYSQL,
      vpc,
      scaling: { autoPause: cdk.Duration.minutes(10), minCapacity: rds.AuroraCapacityUnit.ACU_2, maxCapacity: rds.AuroraCapacityUnit.ACU_32 }, // スケーリング設定
    });

    // DynamoDBテーブルの設定
    const table = new dynamodb.Table(this, 'MyTable', {
      partitionKey: { name: 'id', type: dynamodb.AttributeType.STRING },
    });

    // Lambda関数の設定
    const lambdaFunction = new lambda.Function(this, 'MyLambdaFunction', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'index.handler',
      code: lambda.Code.fromAsset('path/to/your/lambda/code'),
      environment: {
        TABLE_NAME: table.tableName,
        CLUSTER_ARN: cluster.clusterArn,
        SECRET_ARN: cluster.secret?.secretArn || '', // Aurora接続用
      },
    });

    // LambdaにDynamoDBとAuroraへのアクセス権を付与
    table.grantReadWriteData(lambdaFunction);
    cluster.grantDataApiAccess(lambdaFunction);

    // API Gatewayの設定
    const api = new apigateway.LambdaRestApi(this, 'Endpoint', {
      handler: lambdaFunction,
    });
  }
}

const app = new cdk.App();
new MyApplicationStack(app, 'MyApplicationStack');

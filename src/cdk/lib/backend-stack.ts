import {
  Stack,
  StackProps,
  Duration,
} from 'aws-cdk-lib';
import { Construct } from 'constructs'; 
import { EnvProps } from './environment-interface';
import {
  LayerVersion,
  Function,
  Code,
  Runtime,
} from 'aws-cdk-lib/aws-lambda';
import {
  LambdaIntegration,
  PassthroughBehavior,
  MockIntegration,
  IResource,
  RestApi,
} from 'aws-cdk-lib/aws-apigateway';
import {
  Table,
  AttributeType,
} from 'aws-cdk-lib/aws-dynamodb';
import {
  ServerlessCluster,
  DatabaseClusterEngine,
  AuroraCapacityUnit,
} from 'aws-cdk-lib/aws-rds';
import {
  AwsCustomResource,
  AwsCustomResourcePolicy,
  PhysicalResourceId,
} from 'aws-cdk-lib/custom-resources';
import {
  Vpc,
  SecurityGroup,
  Port,
} from 'aws-cdk-lib/aws-ec2';
import { PolicyStatement } from 'aws-cdk-lib/aws-iam';

import {
  createVpc,
  createSecurityGroup
} from './backend/vpc/vpc';

export class BackendStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);
    const env = props?.env as EnvProps;

    // The code that defines your stack goes here
    const vpc: Vpc = createVpc(this, 'AuroraVpc');

    // Lambda関数用のセキュリティグループ
    const lambdaSecurityGroup: SecurityGroup = createSecurityGroup(
      this,
      'LambdaSecurityGroup',
      vpc,
      'Security group for Lambda function',
    );
    const auroraSecurityGroup = createSecurityGroup(
      this,
      'AuroraSecurityGroup',
      vpc,
      'Security group for Aurora Serverless v2',
    );
    // Lambda関数からの接続を許可
    auroraSecurityGroup.addIngressRule(
      lambdaSecurityGroup, 
      Port.tcp(3306), 
      'Allow access from Lambda'
    );

    // Aurora Serverless v2のクラスター設定
    const defaultDatabaseName: string = 'umap_db';
    const cluster = new ServerlessCluster(this, 'AuroraCluster', {
      engine: DatabaseClusterEngine.AURORA_MYSQL,
      vpc,
      scaling: {
        autoPause: Duration.minutes(5),
        minCapacity: AuroraCapacityUnit.ACU_1,
        maxCapacity: AuroraCapacityUnit.ACU_16,
      }, // スケーリング設定
      defaultDatabaseName: defaultDatabaseName,
      securityGroups: [auroraSecurityGroup],
    });

    // Lambdaレイヤーの作成
    const dbProcessLambdaLayer = new LayerVersion(this, 'DBProcessLambdaLayer', {
      code: Code.fromAsset('lib/backend/lambda/python/db_process_lambda_layer.zip'),
      compatibleRuntimes: [Runtime.PYTHON_3_12],
      description: 'A layer containing pymysql',
    });
    // Aurora DBセットアップ用のLambda関数
    const auroraSetupLambda = new Function(this, 'AuroraSetupFunction', {
      runtime: Runtime.PYTHON_3_12, // ランタイムバージョンに注意
      handler: 'bootstrap-function.handler',
      code: Code.fromAsset('lib/backend/lambda/python/resources/auroradb'),
      layers: [dbProcessLambdaLayer], // レイヤーの追加
      vpc: vpc,
      securityGroups: [lambdaSecurityGroup],
      environment: {
        SECRET_ARN: cluster.secret?.secretArn || '', // シークレットのARNを環境変数に追加
        DB_HOST: cluster.clusterEndpoint.hostname,
        DB_NAME: defaultDatabaseName,
      },
      timeout: Duration.seconds(600),
    });
    auroraSetupLambda.addToRolePolicy(new PolicyStatement({
      actions: ['rds-data:*', 'secretsmanager:GetSecretValue'],
      resources: ['*', cluster.secret?.secretArn || ''],
    }));

    // カスタムリソースの定義
    const auroraDbSetup = new AwsCustomResource(this, 'AuroraDBSetup', {
      onCreate: {
        service: 'Lambda',
        action: 'invoke',
        parameters: {
          FunctionName: auroraSetupLambda.functionName,
          // 必要に応じて他のパラメータを追加
        },
        physicalResourceId: PhysicalResourceId.of(Date.now().toString()), // ユニークなID
      },
      policy: AwsCustomResourcePolicy.fromStatements([
        new PolicyStatement({
          actions: ['lambda:InvokeFunction'],
          resources: [auroraSetupLambda.functionArn], // Lambda関数のARNを指定
        })
      ]),
    });


    // DynamoDBテーブルの設定
    const dynamoDBTable = new Table(this, 'DynamoDBTable', {
      partitionKey: {
        name: 'id',
        type: AttributeType.STRING
      },
    });

    // Lambda関数の設定
    // Lambdaレイヤーの作成
    const dataProcessLambdaLayer = new LayerVersion(this, 'DataProcessLambdaLayer', {
      code: Code.fromAsset('lib/backend/lambda/python/data_process_lambda_layer.zip'),
      compatibleRuntimes: [Runtime.PYTHON_3_12],
      description: 'A layer containing onnxruntime, pandas, and numpy',
    });
    // Lambda関数の作成
    const postIdLambdaFunction = new Function(this, 'PostIdLambdaFunction', {
      runtime: Runtime.PYTHON_3_12,
      handler: 'post-id.handler',
      code: Code.fromAsset('lib/backend/lambda/python/codes'),  // new AssetCode("lib/lambda/python/codes")
      // layers: [dataProcessLambdaLayer], // レイヤーの追加
      environment: {
        TABLE_NAME: dynamoDBTable.tableName,
        CLUSTER_ARN: cluster.clusterArn,
        SECRET_ARN: cluster.secret?.secretArn || '', // シークレットのARNを環境変数に追加
        DB_NAME: defaultDatabaseName,
      },
      initialPolicy: [
        new PolicyStatement({
          actions: ['secretsmanager:GetSecretValue'],
          resources: [cluster.secret?.secretArn || ''],
        }),
      ],
      timeout: Duration.seconds(30),
    });

    // LambdaにDynamoDBとAuroraへのアクセス権を付与
    dynamoDBTable.grantReadWriteData(postIdLambdaFunction);
    cluster.grantDataApiAccess(postIdLambdaFunction);

    // API Gatewayの設定
    // const api = new LambdaRestApi(this, 'Endpoint', {
    //   handler: lambdaFunction,
    //   proxy: false,
    // });
    const api = new RestApi(this, "UmapApi", {
      restApiName: "UMap Service",
    });

    const ids = api.root.addResource("id");
    // const singleRoom = ids.addResource("{id}");
    // const getRoomIntegration = new LambdaIntegration(getRoomLambda);
    // const postRoomIntegration = new LambdaIntegration(postRoomLambda);
    // const postIdIntegration: LambdaIntegration = integrateCorsLambda(postIdLambdaFunction);
    const postIdIntegration: LambdaIntegration = new LambdaIntegration(postIdLambdaFunction);
    // const getRoomShowIntegration = new LambdaIntegration(getRoomShowLambda);
    // const postRoomUpdateIntegration = new LambdaIntegration(postRoomUpdateLambda);
    // singleRoom.addMethod("GET", getRoomShowIntegration);
    // singleRoom.addMethod("POST", postRoomUpdateIntegration);
    // ids.addMethod("GET", getRoomIntegration);
    ids.addMethod("POST", postIdIntegration);
  }
}
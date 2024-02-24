import {
  Stack,
  StackProps,
  Duration,
  Aws,
  RemovalPolicy,
} from 'aws-cdk-lib';
import { Construct } from 'constructs'; 
import { EnvProps } from './environment-interface';
import {
  LayerVersion,
  Function,
  Code,
  DockerImageCode,
  Runtime,
} from 'aws-cdk-lib/aws-lambda';
import {
  LambdaIntegration,
  PassthroughBehavior,
  MockIntegration,
  IResource,
  RestApi,
  Resource,
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
  Repository,
} from 'aws-cdk-lib/aws-ecr';
import { DockerImageAsset } from 'aws-cdk-lib/aws-ecr-assets';
import { 
  ECRDeployment,
  DockerImageName,
} from 'cdk-ecr-deployment';

import {
  createVpc,
  createSecurityGroup,
  allowLambdaToAurora,
} from './backend/vpc/vpc';
import {
  createAuroraServerless,
} from './backend/auroradb/auroradb';
import {
  createDBProcessLayer,
  createDataProcessLambdaLayer,
  createAuroraSetupLambda,
  addSecretsManagerPolicy,
  createAuroraDbSetupResource,
  createDBAccessLambdaFunction,
  createDataProcessDBAccessLambdaFunction,
} from './backend/lambda/lambda';
import { createDynamoDBTable } from './backend/dynamodb/dynamodb';
import {
  createRestApi,
  addPostResourcePath,
  addPostResourceParamedPath,
  addGetResourcePath,
  addGetResourceParamedPath,
} from './backend/gateway/gateway';


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
    allowLambdaToAurora(lambdaSecurityGroup, auroraSecurityGroup);

    // Aurora Serverless v2のクラスター設定
    const defaultDatabaseName: string = 'umap_db';
    const cluster = createAuroraServerless(
      this,
      'AuroraServerless',
      vpc,
      defaultDatabaseName,
      auroraSecurityGroup,
    );

    // Lambdaレイヤーの作成
    const dbProcessLambdaLayer = createDBProcessLayer(
      this,
      'DBProcessLambdaLayer',
    );
    // Aurora DBセットアップ用のLambda関数
    const auroraSetupLambda = createAuroraSetupLambda(
      this,
      'AuroraSetupFunction',
      dbProcessLambdaLayer,
      vpc,
      lambdaSecurityGroup,
      cluster,
      defaultDatabaseName,
    );
    addSecretsManagerPolicy(auroraSetupLambda, cluster);

    // カスタムリソースの定義
    const auroraDbSetup = createAuroraDbSetupResource(
      this,
      'AuroraDbSetup',
      auroraSetupLambda,
    );


    // DynamoDBテーブルの設定
    const tableName: string = 'message_table';
    const dynamoDBTable = createDynamoDBTable(
      this,
      'DynamoDBTable',
      tableName,
    );


    // Lambda関数の設定
    const environment: { [key: string]: any } = {
      TABLE_NAME: dynamoDBTable.tableName,
      CLUSTER_ARN: cluster.clusterArn,
      SECRET_ARN: cluster.secret?.secretArn || '', // シークレットのARNを環境変数に追加
      DB_NAME: defaultDatabaseName,
    };
    // API Gatewayの設定
    const api = createRestApi(this, "UmapApi", "UMap Service");

    // Lambdaレイヤーの作成
    // const dataProcessLambdaLayer = createDataProcessLambdaLayer(
    //   this,
    //   'DataProcessLambdaLayer',
    // );

    // Lambda関数の作成
    const postIdLambdaFunction = createDBAccessLambdaFunction(
      this,
      'PostIdLambdaFunction',
      'post-id.handler',
      Code.fromAsset('lib/backend/lambda/python/codes'),
      environment,
      cluster,
      dynamoDBTable,
    );
    const postIdLambdaIntegration: LambdaIntegration = new LambdaIntegration(postIdLambdaFunction);
    const ids: Resource = addPostResourcePath(api, "ids", postIdLambdaIntegration);

    const PostCsvDockerLambdaFunction = createDataProcessDBAccessLambdaFunction(
      this,
      'PostCsvDockerLambdaFunction',
      DockerImageCode.fromImageAsset('lib/backend/lambda/python/dockers/post-csv'),
      environment,
      cluster,
      dynamoDBTable,
    );
    const postCsvDockerLambdaIntegration: LambdaIntegration = new LambdaIntegration(PostCsvDockerLambdaFunction);
    const csvs = addPostResourcePath(api, "csv", postCsvDockerLambdaIntegration);

    const postAccountLambdaFunction = createDBAccessLambdaFunction(
      this,
      'PostAccountLambdaFunction',
      'post-account.handler',
      Code.fromAsset('lib/backend/lambda/python/codes'),
      environment,
      cluster,
      dynamoDBTable,
    );
    const postAccountLambdaIntegration: LambdaIntegration = new LambdaIntegration(postAccountLambdaFunction);
    const account: Resource = addPostResourcePath(api, "account", postAccountLambdaIntegration);

    const getItemsLambdaFunction = createDBAccessLambdaFunction(
      this,
      'getItemsLambdaFunction',
      'get-items.handler',
      Code.fromAsset('lib/backend/lambda/python/codes'),
      environment,
      cluster,
      dynamoDBTable,
    );
    const getItemsLambdaIntegration: LambdaIntegration = new LambdaIntegration(getItemsLambdaFunction);
    const items: Resource = addGetResourcePath(api, "items", getItemsLambdaIntegration);

    const postDataStructureLambdaFunction = createDBAccessLambdaFunction(
      this,
      'postDataStructureLambdaFunction',
      'post-data-structure.handler',
      Code.fromAsset('lib/backend/lambda/python/codes'),
      environment,
      cluster,
      dynamoDBTable,
    );
    const postDataStructureLambdaIntegration: LambdaIntegration = new LambdaIntegration(postDataStructureLambdaFunction);
    const dataStructure: Resource = addPostResourcePath(api, "data_structure", postDataStructureLambdaIntegration);

    const postDataToOrganizationDockerLambdaFunction = createDataProcessDBAccessLambdaFunction(
      this,
      'PostDataToOrganizationDockerLambdaFunction',
      DockerImageCode.fromImageAsset('lib/backend/lambda/python/dockers/post-data-to-organization'),
      environment,
      cluster,
      dynamoDBTable,
    );
    const postDataToOrganizationDockerLambdaIntegration: LambdaIntegration = new LambdaIntegration(postDataToOrganizationDockerLambdaFunction);
    const data: Resource = api.root.addResource("data");
    const dataToOrganization: Resource = data.addResource("{organization_id}");
    dataToOrganization.addMethod("POST", postDataToOrganizationDockerLambdaIntegration);
    
    const getNearItemsLambdaFunction = createDBAccessLambdaFunction(
      this,
      'getNearItemsLambdaFunction',
      'get-near-items.handler',
      Code.fromAsset('lib/backend/lambda/python/codes'),
      environment,
      cluster,
      dynamoDBTable,
    );
    const getNearItemsLambdaIntegration: LambdaIntegration = new LambdaIntegration(getNearItemsLambdaFunction);
    const nearItems: Resource = addGetResourcePath(api, "near_items", getNearItemsLambdaIntegration);

    const getRecommendItemsLambdaFunction = createDBAccessLambdaFunction(
      this,
      'getRecommendItemsLambdaFunction',
      'get-recommend-items.handler',
      Code.fromAsset('lib/backend/lambda/python/codes'),
      environment,
      cluster,
      dynamoDBTable,
    );
    const getRecommendItemsLambdaIntegration: LambdaIntegration = new LambdaIntegration(getRecommendItemsLambdaFunction);
    const recommendItems: Resource = addGetResourcePath(api, "recommend_items", getRecommendItemsLambdaIntegration);

    // TODO: Rename resource when replace
    const postQuestionToItemLambdaFunction = createDBAccessLambdaFunction(
      this,
      'postQuestionToItemLambdaFunction',
      'post-question-to-item.handler',
      Code.fromAsset('lib/backend/lambda/python/codes'),
      environment,
      cluster,
      dynamoDBTable,
    );
    const postQuestionToItemLambdaIntegration: LambdaIntegration = new LambdaIntegration(postQuestionToItemLambdaFunction);
    const question: Resource = api.root.addResource("question_prime");
    // const questionToItem: Resource = question.addResource("{item_id}");
    const questionToId: Resource = question.addResource("{id}");
    questionToId.addMethod("POST", postQuestionToItemLambdaIntegration);

    const getQuestionsLambdaFunction = createDBAccessLambdaFunction(
      this,
      'getQuestionsLambdaFunction',
      'get-questions.handler',
      Code.fromAsset('lib/backend/lambda/python/codes'),
      environment,
      cluster,
      dynamoDBTable,
    );
    const getQuestionsLambdaIntegration: LambdaIntegration = new LambdaIntegration(getQuestionsLambdaFunction);
    const questions: Resource = addGetResourcePath(api, "questions", getQuestionsLambdaIntegration);

    // TODO: Rename resource when replace
    const getQuestionLambdaFunction = createDBAccessLambdaFunction(
      this,
      'getQuestionLambdaFunction',
      'get-question.handler',
      Code.fromAsset('lib/backend/lambda/python/codes'),
      environment,
      cluster,
      dynamoDBTable,
    );
    const getQuestionLambdaIntegration: LambdaIntegration = new LambdaIntegration(getQuestionLambdaFunction);
    questionToId.addMethod("GET", getQuestionLambdaIntegration);

    const getMultiEmotionDockerLambdaFunction = createDataProcessDBAccessLambdaFunction(
      this,
      'getMultiEmotionDockerLambdaFunction',
      DockerImageCode.fromImageAsset('lib/backend/lambda/python/dockers/get-multi-emotion'),
      environment,
      cluster,
      dynamoDBTable,
      Duration.seconds(120),
      2048,
    );
    const getMultiEmotionDockerLambdaIntegration: LambdaIntegration = new LambdaIntegration(getMultiEmotionDockerLambdaFunction);
    const multi_emotion: Resource = addGetResourcePath(api, "multi_emotion", getMultiEmotionDockerLambdaIntegration);

    const postAnswerToQuestionLambdaFunction = createDBAccessLambdaFunction(
      this,
      'postAnswerToQuestionLambdaFunction',
      'post-answer-to-question.handler',
      Code.fromAsset('lib/backend/lambda/python/codes'),
      environment,
      cluster,
      dynamoDBTable,
    );
    const postAnswerToQuestionLambdaIntegration: LambdaIntegration = new LambdaIntegration(postAnswerToQuestionLambdaFunction);
    const answer: Resource = api.root.addResource("answer");
    const answerToId: Resource = answer.addResource("{id}");
    answerToId.addMethod("POST", postAnswerToQuestionLambdaIntegration);
  }
}

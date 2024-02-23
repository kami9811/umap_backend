import { Construct } from 'constructs'
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { ServerlessCluster } from 'aws-cdk-lib/aws-rds';

class Auroradb extends Construct {
  constructor(scope: Construct, id: string) {
    super(scope, id);

    
  }
}
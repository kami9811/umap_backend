import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { aws_amplify as amplify } from 'aws-cdk-lib';

export class CdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create Amplify App
    const amplifyApp = new amplify.CfnApp(this, 'UMapApp', {
      name: 'UMapApp',
      repository: '',
      oauthToken: '',
    });
  }
}

import { 
  App, 
  StackProps,
} from 'aws-cdk-lib';
import { Construct } from 'constructs';
// import { aws_amplify as amplify } from 'aws-cdk-lib';
import {
  CfnApp,
  CfnBranch,
} from 'aws-cdk-lib/aws-amplify';
import { CmsAmplifyProps } from './cms-amplify-interface';

export class CmsAmplify extends Construct {
  constructor(scope: Construct, id: string, props: CmsAmplifyProps) {
    super(scope, id);

    // const env = getAppEnvironment();

    // Create Amplify App
    const amplifyApp = new CfnApp(this, 'UMapCmsApp', {
      name: 'UMapCmsApp',
      repository: props.amplifyRepositoryUrl ?? '',
      oauthToken: props.amplifyOauthToken,
    });

    new CfnBranch(this, 'UMapCmsAppBranch', {
      appId: amplifyApp.ref,
      branchName: props.amplifyBranch,
      enableAutoBuild: true,
    });
  }
}

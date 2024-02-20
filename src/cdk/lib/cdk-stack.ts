import {
  Stack,
  StackProps,
} from 'aws-cdk-lib';
import { Construct } from 'constructs'; 
import { EnvProps } from './environment-interface';
import { CmsAmplify } from './amplify/cms-amplify';
import { CmsAmplifyProps } from './amplify/cms-amplify-interface';

export class CdkStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);
    const env = props?.env as EnvProps;

    // The code that defines your stack goes here
    const amplify_env: CmsAmplifyProps = {
      amplifyRepositoryUrl: env.amplifyRepositoryUrl,
      amplifyOauthToken: env.amplifyOauthToken,
      amplifyBranch: env.amplifyBranch,
    };
    new CmsAmplify(
      this, 
      'CmsAmplifyStack', 
      amplify_env,
    );
    
  }
}

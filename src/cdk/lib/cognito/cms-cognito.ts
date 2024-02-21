import { Construct } from 'constructs';
import {
  UserPool,
  UserPoolClient,
} from 'aws-cdk-lib/aws-cognito';

export class CmsCognito extends Construct {
  constructor(scope: Construct, id: string) {
    super(scope, id);

    // Cognito User Poolの作成
    const userPool: UserPool = new UserPool(this, 'MyUserPool', {
      selfSignUpEnabled: true, // ユーザー自身によるサインアップを許可
      autoVerify: { email: true }, // Eメールによる自動認証を有効化
      signInAliases: { email: true }, // サインインにEメールを使用
    });

    // アプリクライアントの作成 (オプションで設定可能)
    const userPoolClient: UserPoolClient = new UserPoolClient(this, 'AppClient', {
      userPool,
      authFlows: {
        userPassword: true, // パスワード認証を許可
        userSrp: true // SRP認証を許可
      }
    });
  }
}

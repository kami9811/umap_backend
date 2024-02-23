import { 
  Vpc,
  SecurityGroup,
  Port,
} from 'aws-cdk-lib/aws-ec2';
import { Construct } from 'constructs';

export function createVpc(scope: Construct, id: string): Vpc {
  // VPCの設定（Aurora Serverless v2では必要です）
  return new Vpc(scope, id);
}

export function createSecurityGroup(
  scope: Construct, 
  id: string, 
  vpc: Vpc, 
  description: string, 
  allowAllOutbound: boolean = true,
): SecurityGroup {
  return new SecurityGroup(scope, id, {
    vpc,
    description,
    allowAllOutbound,
  });
}

export function allowLambdaToAurora(
  lambdaSecurityGroup: SecurityGroup, 
  auroraSecurityGroup: SecurityGroup,
): void {
  auroraSecurityGroup.addIngressRule(
    lambdaSecurityGroup, 
    Port.tcp(3306),
    'Allow access from Lambda'
  );
}

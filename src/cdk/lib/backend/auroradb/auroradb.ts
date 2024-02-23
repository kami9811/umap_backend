import { Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs'
import {
  ServerlessCluster,
  AuroraCapacityUnit,
  DatabaseClusterEngine,
} from 'aws-cdk-lib/aws-rds';
import {
  Vpc,
  SecurityGroup,
} from 'aws-cdk-lib/aws-ec2';

export function createAuroraServerless(
  scope: Construct,
  id: string,
  vpc: Vpc,
  defaultDatabaseName: string,
  auroraSecurityGroup: SecurityGroup,
): ServerlessCluster {
  return new ServerlessCluster(scope, id, {
    engine: DatabaseClusterEngine.AURORA_MYSQL,
    vpc,
    scaling: {
      autoPause: Duration.minutes(5),
      minCapacity: AuroraCapacityUnit.ACU_1,
      maxCapacity: AuroraCapacityUnit.ACU_16,
    },
    defaultDatabaseName: defaultDatabaseName,
    securityGroups: [auroraSecurityGroup],
  });
}
import { Construct } from 'constructs';
import {
  Table,
  AttributeType,
} from 'aws-cdk-lib/aws-dynamodb';


export function createDynamoDBTable(
  scope: Construct,
  id: string,
  tableName: string,
): Table {
  return new Table(scope, id, {
    partitionKey: {
      name: 'id',
      type: AttributeType.STRING,
    },
    tableName: tableName,
  });
}

import json
import boto3
from botocore.config import Config
import os

# Initialize RDS Data Service client with custom timeouts
rds_config = Config(
    read_timeout=90,  # Set read timeout to 90 seconds
    connect_timeout=30,  # Set connection timeout to 30 seconds
    retries={'max_attempts': 5}  # Enable retries with a reasonable number of attempts
)
rds_data = boto3.client('rds-data', config=rds_config)

# Environment variables
CLUSTER_ARN = os.environ['CLUSTER_ARN']
SECRET_ARN = os.environ['SECRET_ARN']
DB_NAME = os.environ['DB_NAME']

def handler(event, context):
    # Parse query parameters
    query_params = event['queryStringParameters']
    organization_id = query_params.get('organization_id', '')

    # SQL to check if items with the specified organization_id exist
    sql = f"SELECT EXISTS (SELECT 1 FROM ITEMS WHERE organization_id = :organization_id)"
    parameters = [
        {'name': 'organization_id', 'value': {'stringValue': organization_id}}
    ]
    
    # Execute SQL query
    response = rds_data.execute_statement(
        database=DB_NAME,
        resourceArn=CLUSTER_ARN,
        secretArn=SECRET_ARN,
        sql=sql,
        parameters=parameters,
        includeResultMetadata=True
    )
    
    # Determine if items exist based on the SQL query result
    items_exist = 0
    if response['records'] and response['records'][0][0]['longValue'] == 1:
        items_exist = 1
    
    # Return the appropriate response
    return {
        'statusCode': 200,
        'body': json.dumps({
            'status': 200,
            'items_exist': items_exist,
            'message': 'Items exist' if items_exist else 'No items exist'
        }),
        'headers': {
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": '*',
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
        },
    }

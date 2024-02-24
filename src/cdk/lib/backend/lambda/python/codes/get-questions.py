import json
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import os
import time
import random

# Environment variables
CLUSTER_ARN = os.environ['CLUSTER_ARN']
SECRET_ARN = os.environ['SECRET_ARN']
DB_NAME = os.environ['DB_NAME']

# Initialize RDS Data Service client
rds_config = Config(
    read_timeout=90,
    connect_timeout=30,
    retries={'max_attempts': 5}
)
rds_data = boto3.client('rds-data', config=rds_config)

def execute_statement_with_retry(rds_data, sql, parameters, max_attempts=5, base_delay=2.0, max_delay=30.0):
    attempt = 0
    while attempt < max_attempts:
        try:
            response = rds_data.execute_statement(
                database=DB_NAME,
                resourceArn=CLUSTER_ARN,
                secretArn=SECRET_ARN,
                sql=sql,
                parameters=parameters
            )
            return response
        except ClientError as e:
            print(f"Attempt {attempt + 1} failed with error: {e}")
            attempt += 1
            if attempt >= max_attempts:
                raise
            
            delay = min(max_delay, base_delay * 2 ** attempt)
            delay_with_jitter = delay / 2 + random.uniform(0, delay / 2)
            print(f"Retrying in {delay_with_jitter:.2f} seconds...")
            time.sleep(delay_with_jitter)

# TODO: Fix for org merge search based on organization_id
def handler(event, context):
    # Retrieve query parameters
    query_params = event['queryStringParameters']
    item_id = query_params.get('item_id', None)
    organization_id = query_params.get('organization_id', None)

    # SQL query preparation
    base_sql = "SELECT id, question_title FROM QUESTIONS"
    conditions = []
    parameters = []
    
    if item_id:
        conditions.append("item_id = :item_id")
        parameters.append({'name': 'item_id', 'value': {'longValue': int(item_id)}})
    if organization_id:
        conditions.append("organization_id = :organization_id")
        # organization_id is string type
        parameters.append({'name': 'organization_id', 'value': {'stringValue': organization_id}})
        # parameters.append({'name': 'organization_id', 'value': {'longValue': int(organization_id)}})
    
    if conditions:
        sql = f"{base_sql} WHERE {' AND '.join(conditions)}"
    else:
        sql = base_sql

    # Execute SQL query
    try:
        response = execute_statement_with_retry(rds_data, sql, parameters)
        questions = [{"question_id": record[0]['longValue'], "question_title": record[1]['stringValue']}
                     for record in response['records']]
        
        response_message = {
            "status": 200,
            "questions": questions,
            "message": "Questions fetched successfully"
        }
        status_code = 200
    except Exception as e:
        response_message = {
            "status": 400,
            "message": "Error fetching questions: " + str(e)
        }
        status_code = 400

    return {
        'statusCode': status_code,
        'body': json.dumps(response_message),
        'headers': {
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": '*',
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
        },
    }

import json
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import os
import time
import random

# Initialize RDS Data Service client with environment variables
CLUSTER_ARN = os.environ['CLUSTER_ARN']
SECRET_ARN = os.environ['SECRET_ARN']
DB_NAME = os.environ['DB_NAME']

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

def handler(event, context):
    # Extract question_id from the event path parameters
    question_id = event['pathParameters']['id']

    # SQL to join QUESTIONS and ANSWERS tables and select required fields
    sql = """
    SELECT q.question_title, q.question_text, a.id AS answer_id, a.answer_text
    FROM QUESTIONS q
    LEFT JOIN ANSWERS a ON q.id = a.question_id
    WHERE q.id = :question_id
    """

    parameters = [
        {'name': 'question_id', 'value': {'longValue': int(question_id)}}
    ]

    try:
        response = execute_statement_with_retry(rds_data, sql, parameters)
        records = response['records']

        question_title = question_text = ""
        answers = []

        for record in records:
            if not question_title or not question_text:  # Assuming these are the same for all rows
                question_title = record[0]['stringValue']
                question_text = record[1]['stringValue']
            if record[2]:  # If there is an answer
                answers.append({
                    "answer_id": None if next(iter(record[2].values())) == True else record[2]['longValue'],
                    "answer_text": None if next(iter(record[3].values())) == True else record[3]['stringValue']
                })

        response_body = {
            "status": 200,
            "question_title": question_title,
            "question_text": question_text,
            "answers": answers,
            "message": "Successfully fetched question and answers"
        }
        
        status_code = 200
    except Exception as e:
        print(e)
        response_body = {
            "status": 400,
            "message": str(e)
        }
        status_code = 400

    return {
        'statusCode': status_code,
        'body': json.dumps(response_body),
        'headers': {
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": '*',
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
        },
    }

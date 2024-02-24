import json
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import os
import time
import random

# 環境変数からリソース名を取得
CLUSTER_ARN = os.environ['CLUSTER_ARN']
SECRET_ARN = os.environ['SECRET_ARN']
DB_NAME = os.environ['DB_NAME']

# RDS Data Serviceクライアントの初期化
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
    body = json.loads(event['body'])
    question_id = body['question_id']
    answer_user = body['answer_user']
    answer_text = body['answer_text']

    # SQL文の準備
    sql = """
    INSERT INTO ANSWERS (question_id, answer_user, answer_text) 
    VALUES (:question_id, :answer_user, :answer_text)
    """

    # パラメータの準備
    parameters = [
        {'name': 'question_id', 'value': {'longValue': int(question_id)}},  # Assuming question_id is an integer
        {'name': 'answer_user', 'value': {'stringValue': answer_user}},
        {'name': 'answer_text', 'value': {'stringValue': answer_text}}
    ]

    try:
        response = execute_statement_with_retry(
            rds_data,
            sql,
            parameters,
        )
        response_message = "記録に成功しました．"
        status_code = 200
    except Exception as e:
        response_message = str(e)
        status_code = 400

    return {
        'statusCode': status_code,
        'body': json.dumps({'message': response_message}),
        'headers': {
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": '*',
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
        },
    }

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
    read_timeout=90,  # 読み込みタイムアウトを90秒に設定
    connect_timeout=30,  # 接続タイムアウトを30秒に設定
    retries={'max_attempts': 5}  # リトライ回数を5回に設定
)
rds_data = boto3.client('rds-data', config=rds_config)

def execute_statement_with_retry(
    rds_data, 
    sql,
    parameters,
    max_attempts=5,
    base_delay=1.0, 
    max_delay=30.0
):
    attempt = 0
    while attempt < max_attempts:
        try:
            # Aurora DBへのクエリを試行
            response = rds_data.execute_statement(
                database=DB_NAME,
                resourceArn=CLUSTER_ARN,
                secretArn=SECRET_ARN,
                sql=sql,
                parameters=parameters
            )
            return response  # 成功した場合はレスポンスを返す
        except ClientError as e:
            # 特定のエラーに基づいてリトライを決定することも可能
            print(f"Attempt {attempt + 1} failed with error: {e}")
            attempt += 1
            if attempt >= max_attempts:
                raise  # 最大試行回数に達した場合はエラーを再投げる
            
            # 指数バックオフとジッターを使った遅延
            delay = min(max_delay, base_delay * 2 ** attempt)
            delay_with_jitter = delay / 2 + random.uniform(0, delay / 2)
            print(f"Retrying in {delay_with_jitter:.2f} seconds...")
            time.sleep(delay_with_jitter)

def handler(event, context):
    # API Gatewayからのリクエストボディを解析
    body = json.loads(event['body'])
    organization_id = body['organization_id']
    data_attributes = json.dumps(body['data_attributes'])  # JSONオブジェクトを文字列に変換
    is_abstract_data = json.dumps(body['is_abstract_data'])  # JSONオブジェクトを文字列に変換

    # SQL文の準備
    sql = """
    UPDATE ORGANIZATIONS
    SET data_attributes = :data_attributes, is_abstract_data = :is_abstract_data
    WHERE id = :organization_id
    """

    # パラメータの準備
    parameters = [
        {'name': 'organization_id', 'value': {'stringValue': organization_id}},
        {'name': 'data_attributes', 'value': {'stringValue': data_attributes}},
        {'name': 'is_abstract_data', 'value': {'stringValue': is_abstract_data}}
    ]

    # Aurora DBに対してSQL文を実行
    try:
        # rds_data.execute_statement(
        #     database=DB_NAME,
        #     resourceArn=CLUSTER_ARN,
        #     secretArn=SECRET_ARN,
        #     sql=sql,
        #     parameters=parameters
        # )
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

    # レスポンスの生成
    return {
        'statusCode': status_code,
        'body': json.dumps({'message': response_message}),
        'headers': {
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": '*',
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
        },
    }

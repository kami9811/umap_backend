import json
import boto3
from botocore.config import Config
import os

# 環境変数からリソース名を取得
TABLE_NAME = os.environ['TABLE_NAME']
CLUSTER_ARN = os.environ['CLUSTER_ARN']
SECRET_ARN = os.environ['SECRET_ARN']

# Boto3クライアントの初期化
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

# RDS Data Serviceクライアントの初期化
# カスタムタイムアウト設定
rds_config = Config(
    read_timeout=90, # 読み取りタイムアウトを90秒に設定
    connect_timeout=30, # 接続タイムアウトを30秒に設定
    retries={'max_attempts': 0}  # リトライは無効化（必要に応じて調整）
)
# カスタム設定を使用してRDS Data Serviceクライアントを初期化
rds_data = boto3.client('rds-data', config=rds_config)

def handler(event, context):
    # API Gatewayからのリクエストボディを解析
    body = json.loads(event['body'])
    id = body['id']
    json_data = body['json_data']

    rds_database_name = os.environ['DB_NAME']
    rds_table_name = "example_table"
    
    # DynamoDBにIDを保存
    table.put_item(Item={'id': id})
    
    # Aurora DBにIDとJSONデータを保存
    sql = f"INSERT INTO {rds_table_name} (id, json_data) VALUES (:id, :json_data)"
    parameters = [
        {'name':'id', 'value':{'stringValue': id}},
        {'name':'json_data', 'value':{'stringValue': json.dumps(json_data)}}
    ]
    print(parameters)
    
    rds_data.execute_statement(
        database=rds_database_name,
        resourceArn=CLUSTER_ARN,
        secretArn=SECRET_ARN,
        sql=sql,
        parameters=parameters,
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Data successfully saved to DynamoDB and Aurora DB'
        }),
        'headers': {
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": '*',
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
        },
    }

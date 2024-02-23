import json
import boto3
from botocore.config import Config
import os

# 環境変数からリソース名を取得
TABLE_NAME = os.environ['TABLE_NAME']
CLUSTER_ARN = os.environ['CLUSTER_ARN']
SECRET_ARN = os.environ['SECRET_ARN']
DB_NAME = os.environ['DB_NAME']

# RDS Data Serviceクライアントの初期化
rds_config = Config(
    read_timeout=90,  # Set read timeout to 90 seconds
    connect_timeout=30,  # Set connection timeout to 30 seconds
    retries={'max_attempts': 5}  # Enable retries with a reasonable number of attempts
)
rds_data = boto3.client('rds-data', config=rds_config)

def handler(event, context):
    body = json.loads(event['body'])
    email = body['email']
    organization_id = body['organization_id']
    
    # ORGANIZATIONSにidが存在するか確認
    check_org_sql = "SELECT COUNT(*) AS count FROM ORGANIZATIONS WHERE id = :organization_id"
    check_org_params = [{'name':'organization_id', 'value':{'stringValue': organization_id}}]
    
    org_res = rds_data.execute_statement(
        database=DB_NAME,
        resourceArn=CLUSTER_ARN,
        secretArn=SECRET_ARN,
        sql=check_org_sql,
        parameters=check_org_params
    )
    
    organization_exist = org_res['records'][0][0]['longValue'] == 1
    
    # 存在しない場合はORGANIZATIONSに登録
    if not organization_exist:
        insert_org_sql = "INSERT INTO ORGANIZATIONS (id) VALUES (:organization_id)"
        rds_data.execute_statement(
            database=DB_NAME,
            resourceArn=CLUSTER_ARN,
            secretArn=SECRET_ARN,
            sql=insert_org_sql,
            parameters=check_org_params
        )
    
    # USERSにemailが存在するか確認
    check_user_sql = "SELECT COUNT(*) AS count FROM USERS WHERE email = :email"
    check_user_params = [{'name':'email', 'value':{'stringValue': email}}]
    
    user_res = rds_data.execute_statement(
        database=DB_NAME,
        resourceArn=CLUSTER_ARN,
        secretArn=SECRET_ARN,
        sql=check_user_sql,
        parameters=check_user_params
    )
    
    email_exist = user_res['records'][0][0]['longValue'] == 1
    
    # 存在しない場合はUSERSに登録
    if not email_exist:
        insert_user_sql = "INSERT INTO USERS (email, organization_id) VALUES (:email, :organization_id)"
        rds_data.execute_statement(
            database=DB_NAME,
            resourceArn=CLUSTER_ARN,
            secretArn=SECRET_ARN,
            sql=insert_user_sql,
            parameters=[{'name':'email', 'value':{'stringValue': email}},
                        {'name':'organization_id', 'value':{'stringValue': organization_id}}]
        )
    
    # レスポンスの生成
    response = {
        'status': 200,
        'email_exist': int(email_exist),
        'organization_exist': int(organization_exist),
        'message': 'The account information has been processed.'
    }
    
    return {
        'statusCode': 200,
        'body': json.dumps(response),
        'headers': {
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": '*',
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
        },
    }

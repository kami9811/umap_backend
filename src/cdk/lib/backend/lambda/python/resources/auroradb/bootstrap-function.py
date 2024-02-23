import json
import pymysql
import os
import boto3


def get_db_credentials(secret_arn):
    # Secrets Managerクライアントの作成
    client = boto3.client('secretsmanager')

    # シークレットの値を取得
    response = client.get_secret_value(SecretId=secret_arn)
    if 'SecretString' in response:
        secret = response['SecretString']
        secret_dict = json.loads(secret)
        return secret_dict['username'], secret_dict['password']
    else:
        raise Exception("Secret does not have a SecretString.")

def handler(event, context):
    try:
        # 環境変数からシークレットのARNを取得
        secret_arn = os.environ['SECRET_ARN']
        # データベースの認証情報を取得
        user, password = get_db_credentials(secret_arn)

        # 環境変数から接続情報を取得
        host = os.environ['DB_HOST']
        database = os.environ['DB_NAME']

        # データベースに接続
        conn = pymysql.connect(
            host=host, 
            user=user, 
            passwd=password, 
            db=database, 
            connect_timeout=600,
        )
        with conn.cursor() as cursor:
            # データベースの作成（存在しない場合）
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database};")
            
            # データベースを指定
            cursor.execute(f"USE {database};")
            
            # テーブルの作成（存在しない場合）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS example_table (
                    id VARCHAR(255) NOT NULL PRIMARY KEY,
                    json_data JSON NOT NULL
                );
            """)
            conn.commit()
    except Exception as e:
        print(e)
        return {
            'statusCode': 400,
            'body': json.dumps('Error creating database and table')
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps('Successfully created database and table')
    }

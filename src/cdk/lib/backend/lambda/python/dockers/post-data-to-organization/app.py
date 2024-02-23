import base64
import pandas as pd
from io import StringIO
import json
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import os
import time
import random

# Initialize AWS RDS Data Service client
rds_config = Config(read_timeout=90, connect_timeout=30, retries={'max_attempts': 5})
rds_data = boto3.client('rds-data', config=rds_config)

# Environment variables (ensure these are set in your Lambda function)
CLUSTER_ARN = os.environ['CLUSTER_ARN']
SECRET_ARN = os.environ['SECRET_ARN']
DB_NAME = os.environ['DB_NAME']

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

def get_data_attributes(organization_id):
    # SQL to fetch data attributes for the organization
    sql = "SELECT data_attributes FROM ORGANIZATIONS WHERE id = :organization_id"
    parameters = [{'name': 'organization_id', 'value': {'stringValue': organization_id}}]
    
    # response = rds_data.execute_statement(
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
    # Assuming the response includes the data attributes in the expected format
    print(response)
    data_attributes = json.loads(response['records'][0][0]['stringValue'])
    print(data_attributes)
    # return data_attributes['data_attributes']
    return data_attributes

def insert_items(organization_id, processed_df):
    for _, row in processed_df.iterrows():
        data_values = row.to_json()
        sql = "INSERT INTO ITEMS (organization_id, data_values) VALUES (:organization_id, :data_values)"
        parameters = [
            {'name': 'organization_id', 'value': {'stringValue': organization_id}},
            {'name': 'data_values', 'value': {'stringValue': data_values}}
        ]
        
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

def convert_dataframe_types(df, data_attributes):
    for column, dtype in data_attributes.items():
        if column in df.columns:
            df[column] = df[column].astype(dtype)
    return df

def handler(event, context):
    # Extract organization_id from the path parameter
    organization_id = event['pathParameters']['organization_id']
    print(organization_id)
    
    # Decode the base64 CSV data from the event body
    base64_csv_string = json.loads(event['body'])['csvData']
    csv_string = base64.b64decode(base64_csv_string).decode('utf-8')
    csv_df = pd.read_csv(StringIO(csv_string))
    
    # Fetch data_attributes for the specified organization
    data_attributes = get_data_attributes(organization_id)
    
    # Filter and convert DataFrame according to data_attributes
    filtered_df = csv_df.filter(items=data_attributes.keys())
    processed_df = convert_dataframe_types(filtered_df, data_attributes)
    
    # Insert processed data into ITEMS table
    insert_items(organization_id, processed_df)
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Data successfully processed and saved.'}),
        'headers': {
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": '*',
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
        },
    }

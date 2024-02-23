import json
import boto3
from botocore.config import Config
from math import radians, cos, sin, sqrt, atan2
import os
import time

# 環境変数から情報を取得
CLUSTER_ARN = os.environ['CLUSTER_ARN']
SECRET_ARN = os.environ['SECRET_ARN']
DB_NAME = os.environ['DB_NAME']

# RDS Data Serviceクライアントの初期化
rds_data = boto3.client('rds-data', config=Config(read_timeout=90, connect_timeout=30, retries={'max_attempts': 5}))

def calculate_distance(lat1, lon1, lat2, lon2):
    # 地球の半径（キロメートル）
    R = 6371.0

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance

def execute_statement_with_retry(sql, parameters, max_attempts=5, base_delay=4.0, max_delay=30.0):
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
        except Exception as e:
            print(f"Attempt {attempt + 1} failed with error: {e}")
            attempt += 1
            if attempt >= max_attempts:
                raise
            time.sleep(min(max_delay, base_delay * 2 ** attempt))

def handler(event, context):
    # クエリパラメータから必要な情報を取得
    query_params = event['queryStringParameters']
    organization_id = query_params['organization_id']
    latitude = float(query_params['latitude'])
    longitude = float(query_params['longitude'])

    # ITEMSから指定されたorganization_idに関連する全アイテムを取得
    sql_items = f"""
    SELECT id, data_values, is_abstract_data
    FROM ITEMS
    WHERE organization_id = :organization_id
    """
    parameters_items = [{'name': 'organization_id', 'value': {'stringValue': organization_id}}]

    response_items = execute_statement_with_retry(sql_items, parameters_items)
    items = response_items['records']

    # 距離に基づいてアイテムをフィルタリングしてソート
    sorted_items = []
    for item in items:
        item_data = json.loads(item[1]['stringValue'])  # data_values列
        item_lat = item_data['緯度']
        item_lon = item_data['経度']
        distance = calculate_distance(latitude, longitude, item_lat, item_lon)
        sorted_items.append((item, distance))

    # 距離でソートし、最も近い5つのアイテムを選択
    sorted_items.sort(key=lambda x: x[1])
    nearest_items = sorted_items[:5]

    # 結果を整形
    print(nearest_items)
    result_items = [{
        "data_values": json.loads(item[0][1]['stringValue']),
        "is_abstract_data": json.loads(item[0][2]['stringValue'])
    } for item in nearest_items]

    # ORGANIZATIONSからis_abstract_dataを取得
    sql_org = f"""
    SELECT is_abstract_data
    FROM ORGANIZATIONS
    WHERE id = :organization_id
    """
    parameters_org = [{'name': 'organization_id', 'value': {'stringValue': organization_id}}]

    response_org = execute_statement_with_retry(sql_org, parameters_org)
    organization_is_abstract_data = json.loads(response_org['records'][0][0]['stringValue'])

    return {
        'statusCode': 200,
        'body': json.dumps({
            "status": 200,
            "items": result_items,
            "organization_is_abstract_data": organization_is_abstract_data,
            "message": "Successfully retrieved nearest items."
        }),
        'headers': {
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": '*',
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
        },
    }

import json
import boto3
from botocore.config import Config
import os
import time
import random
from math import radians, cos, sin, sqrt, atan2

# Environment variables
CLUSTER_ARN = os.environ['CLUSTER_ARN']
SECRET_ARN = os.environ['SECRET_ARN']
DB_NAME = os.environ['DB_NAME']

# Initialize RDS Data Service client
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

def execute_statement_with_retry(sql, parameters, max_attempts=5, base_delay=2.0, max_delay=30.0):
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
    # Parse query parameters
    query_params = event['queryStringParameters']
    organization_id = query_params['organization_id']
    latitude = float(query_params['latitude'])
    longitude = float(query_params['longitude'])
    spacious = query_params.get('spacious', '0') == '1'
    facility = query_params.get('facility', '0') == '1'
    equipment = query_params.get('equipment', '0') == '1'

    # Construct the base SQL query to fetch items based on criteria
    sql_items_base = f"""
    SELECT id, data_values, is_abstract_data
    FROM ITEMS
    WHERE organization_id = :organization_id
    """
    parameters_items = [{'name': 'organization_id', 'value': {'stringValue': organization_id}}]

    # Append criteria to SQL query based on spacious, facility, equipment flags
    criteria = []
    if spacious:
        criteria.append("JSON_EXTRACT(data_values, '$.\"公園面積_m2\"') IS NOT NULL AND JSON_EXTRACT(data_values, '$.\"公園面積_m2\"') > (SELECT AVG(JSON_EXTRACT(data_values, '$.\"公園面積_m2\"')) FROM ITEMS WHERE organization_id = :organization_id AND JSON_LENGTH(JSON_EXTRACT(data_values, '$.\"公園面積_m2\"')) > 0)")
    if facility:
        criteria.append("CHAR_LENGTH(JSON_UNQUOTE(JSON_EXTRACT(data_values, '$.\"主な施設\"'))) > 10")
    if equipment:
        criteria.append("CHAR_LENGTH(JSON_UNQUOTE(JSON_EXTRACT(data_values, '$.\"主な遊具\"'))) > 10")

    if criteria:
        sql_items_base += " AND (" + " AND ".join(criteria) + ")"
    
    try:
        print(sql_items_base)
        response_items = execute_statement_with_retry(sql_items_base, parameters_items)
        items = response_items['records']
        print(items)

        # Filter and sort items based on distance if there are more than 5 items
        if len(items) > 5:
            items_with_distance = []
            for item in items:
                item_data = json.loads(item[1]['stringValue'])  # data_values column
                item_lat = item_data.get('緯度')
                item_lon = item_data.get('経度')
                if item_lat is not None and item_lon is not None:
                    distance = calculate_distance(latitude, longitude, item_lat, item_lon)
                    items_with_distance.append((item, distance))

            # Sort items by distance
            sorted_items_with_distance = sorted(items_with_distance, key=lambda x: x[1])
            # Pick the closest 5 items
            items = [item[0] for item in sorted_items_with_distance[:5]]

        # Format items for the response
        print(items)
        result_items = []
        for item in items:
            data_values = json.loads(item[1]['stringValue'])
            data_values['item_id'] = item[0]['longValue']
            is_abstract_data = None if next(iter(item[2].values())) == True else json.loads(item[2]['stringValue']) 
            result_items.append({
                "data_values": data_values,
                "is_abstract_data": is_abstract_data
            })
        print(result_items)

        # Fetch organization's is_abstract_data
        sql_org = f"""
        SELECT is_abstract_data
        FROM ORGANIZATIONS
        WHERE id = :organization_id
        """
        parameters_org = [{'name': 'organization_id', 'value': {'stringValue': organization_id}}]
        response_org = execute_statement_with_retry(sql_org, parameters_org)
        organization_is_abstract_data = json.loads(response_org['records'][0][0]['stringValue'])
        print(organization_is_abstract_data)

        return {
            'statusCode': 200,
            'body': json.dumps({
                "status": 200,
                "items": result_items,
                "organization_is_abstract_data": organization_is_abstract_data,
                "message": "Successfully retrieved recommended items."
            }),
            'headers': {
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Origin": '*',
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
            },
        }
    except Exception as e:
        print(f"Error fetching items: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({'message': str(e)}),
            'headers': {
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Origin": '*',
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
            },
        }

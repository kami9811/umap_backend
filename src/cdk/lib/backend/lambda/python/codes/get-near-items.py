import json
import boto3
from botocore.config import Config
from math import radians, cos, sin, sqrt, atan2
import os
import time

# Initialize RDS Data Service client
rds_data = boto3.client('rds-data', config=Config(read_timeout=90, connect_timeout=30, retries={'max_attempts': 5}))

# Environment variables
CLUSTER_ARN = os.environ['CLUSTER_ARN']
SECRET_ARN = os.environ['SECRET_ARN']
DB_NAME = os.environ['DB_NAME']

def calculate_distance(lat1, lon1, lat2, lon2):
    # Approximate radius of earth in km
    R = 6371.0

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance

def execute_statement_with_retry(sql, parameters, max_attempts=5, base_delay=1.0, max_delay=30.0):
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
    query_params = event['queryStringParameters']
    organization_id = query_params['organization_id']
    latitude = float(query_params['latitude'])
    longitude = float(query_params['longitude'])

    sql = """
    SELECT id, data_values, is_abstract_data
    FROM ITEMS
    WHERE organization_id = :organization_id
    """
    parameters = [{'name': 'organization_id', 'value': {'stringValue': organization_id}}]

    response = execute_statement_with_retry(sql, parameters)
    items = response['records']

    # TODO: Acceralate the following code
    # Filter items based on distance
    nearest_items = []
    for item in items:
        item_lat = item['data_values']['latitude']  # Assuming data_values is a dict with latitude
        item_lon = item['data_values']['longitude']  # Assuming data_values is a dict with longitude
        dist = calculate_distance(latitude, longitude, item_lat, item_lon)
        item['distance'] = dist  # Add distance for sorting
        nearest_items.append(item)

    # Sort by distance and select the top 5
    nearest_items.sort(key=lambda x: x['distance'])
    top_items = nearest_items[:5]

    return {
        'statusCode': 200,
        'body': json.dumps({
            'status': 200,
            'items': top_items,
            'message': 'Successfully retrieved nearest items.'
        }),
        'headers': {
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": '*',
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
        },
    }

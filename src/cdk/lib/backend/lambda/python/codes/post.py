import json
from urllib import response
import boto3
import botocore
import os
import random
import string

def handler(event, context):
  # print(event)

  room_id: string = generate_random_name(16)

  dynamoDB = boto3.resource('dynamodb')
  table = dynamoDB.Table('room_status')
  Item = {
    'closed': -1,
    'id': room_id,
    'pushed_id': "-1",
  }
  insert(table, Item)

  table = dynamoDB.Table('room')
  Item = {
    'id': room_id,
    'empowermenter_id': json.loads(event['body'])['user_id'],
    'pushed_id': "-1",
    'empowerment_result': 0,
    'closed': -1,
  }
  insert(table, Item)

  return {
    'statusCode': 200,
    'body': json.dumps({
      'room_id': room_id,
      'message': 'Registered',
    }),
    'headers': {
      "Access-Control-Allow-Headers": "Content-Type",
      "Access-Control-Allow-Origin": '*',
      "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
    },
  }


def insert(table, Item):

  try:
    # print(os.environ['PRIMARY_KEY'])
    response = table.put_item(
      Item = Item
    )
  except botocore.exceptions.ClientError as e:
    print(e.response['Error']['Message'])
  else:
    return response

def generate_random_name(n):
  randlst = [random.choice(string.ascii_letters + string.digits) for i in range(n)]
  return ''.join(randlst)
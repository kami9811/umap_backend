import base64
import pandas as pd
from io import StringIO
import json

def handler(event, context):
    # JSON ペイロードから Base64 エンコードされた CSV データの文字列を取得
    base64_csv_string = json.loads(event['body'])['csvData']
    
    # Base64 エンコードされた文字列をデコードして CSV データを取得
    csv_string = base64.b64decode(base64_csv_string).decode('utf-8')
    
    # 文字列から pandas DataFrame を作成
    csv_data = pd.read_csv(StringIO(csv_string))
    
    # DataFrame の内容を処理（例：単に出力する）
    print(csv_data)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'CSV Processing with pandas Completed'
        }),
        'headers': {
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": '*',
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
        },
    }

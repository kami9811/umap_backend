import json
from onnxruntime import InferenceSession
from transformers import AutoTokenizer
import numpy as np

# Tokenizerの初期化。元のモデルで使用していたTokenizerの設定およびモデルを読み込む
# model_path = "cl-tohoku/bert-base-japanese-whole-word-masking"
model_path = "cl-tohoku/bert-base-japanese-v2"
tokenizer = AutoTokenizer.from_pretrained(
    model_path,
    use_fast=True,
)
# ONNX形式のモデルから推論用モデルを作成
onnx_file = "./model.onnx"
session = InferenceSession(onnx_file)
LABEL_COLUMNS = ['joy', 'sadness', 'anticipation', 'surprise', 'anger', 'fear', 'disgust', 'trust']

def handler(event, context):
    # Retrieve query parameters
    query_params = event['queryStringParameters']
    message = query_params.get('message', None)
    
    # ONNX形式のモデルで推論する際は return_typeを "np" としてnumpy形式のテンソルを返すようにする
    eval_data = tokenizer(
        message,
        padding="max_length",
        max_length=256,
        truncation=True,
        return_tensors="np"
    )
    result = session.run(None, input_feed=dict(eval_data))
    multi_emotion_dict = {
        LABEL_COLUMNS[i]: (1.0 / (1.0 + np.exp(-value)))
        for i, value in enumerate(result[0][0].tolist())
    }
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'emotions': multi_emotion_dict,
            'message': 'Multi Emotion Analysis Completed',
        }),
        'headers': {
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": '*',
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
        },
    }

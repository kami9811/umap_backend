FROM amazon/aws-lambda-python:3.11
ENV TRANSFORMERS_CACHE=/tmp/huggingface/transformers
# 必要なファイルがあればここに記述
COPY app.py requirements.txt model.onnx ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
CMD [ "app.handler" ]

FROM amazon/aws-lambda-python:3.12
# 必要なファイルがあればここに記述
COPY app.py requirements.txt ./
RUN pip install -r requirements.txt
CMD [ "app.handler" ]

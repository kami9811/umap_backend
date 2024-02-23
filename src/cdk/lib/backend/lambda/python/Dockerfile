FROM python:3.12.2-bullseye

WORKDIR /usr/src/
COPY ./ /usr/src/

# パッケージの追加とタイムゾーンの設定
RUN apt-get update && apt-get install -y \
    tzdata \
    zip \
&&  ln -sf /usr/share/zoneinfo/Asia/Tokyo /etc/localtime \
&&  apt-get clean \
&&  rm -rf /var/lib/apt/lists/*

ENV TZ=Asia/Tokyo

RUN python3 -m pip install --upgrade pip
COPY requirements.txt .
# RUN pip install -r requirements.txt

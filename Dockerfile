FROM node:18.17.1

WORKDIR /usr/src
COPY ./src /usr/src

# Docker CLI のインストール
RUN apt-get update && apt-get install -y \
  apt-transport-https \
  ca-certificates \
  curl \
  gnupg-agent \
  software-properties-common && \
  curl -fsSL https://get.docker.com -o get-docker.sh && \
  sh get-docker.sh && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

RUN npm install -g aws-cdk
# npm install コマンドは必要に応じて

# AWS CLI v2 のインストール
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
  unzip awscliv2.zip && \
  ./aws/install && \
  rm -rf awscliv2.zip ./aws

COPY ./.aws /root/.aws

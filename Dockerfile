FROM node:18.17.1-alpine

WORKDIR /usr/src

# General packages
RUN apk update -q
RUN apk add -q --no-cache \
  binutils-gold \
  make \
  g++ \
  gcc \
  gnupg \
  libgcc \
  python3

RUN npm install -g aws-cdk
RUN npm install @aws-cdk/core
RUN npm install @aws-cdk/aws-cognito
RUN npm install @aws-cdk/aws-rds
RUN npm install @aws-cdk/aws-dynamodb
# RUN npm install  @aws-cdk/aws-lambda
RUN npm install @aws-cdk/aws-amplify

# COPY package.json ./

# RUN npm install

# CMD ["npm", "start"]

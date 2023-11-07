FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y default-libmysqlclient-dev g++ openjdk-11-jdk

RUN pip install -r requirements.txt

COPY . .

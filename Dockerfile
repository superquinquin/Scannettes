FROM python:3.9.13-slim
RUN apt-get update && apt-get install zbar-tools -y
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py /
ADD application /application


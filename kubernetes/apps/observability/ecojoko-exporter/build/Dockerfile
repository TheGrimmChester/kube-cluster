FROM python:3.12.7-alpine
RUN mkdir /app
WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt
ENV PYTHONUNBUFFERED 1
COPY .. .
ENTRYPOINT python3 /app/main.py

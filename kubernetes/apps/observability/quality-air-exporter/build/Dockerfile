FROM python:3.12.2-alpine
RUN mkdir /app
WORKDIR /app
COPY requirements.txt .
RUN apk add glib-dev make gcc musl-dev
RUN pip3 install -r requirements.txt
ENV PYTHONUNBUFFERED 1
COPY main.py /app/main.py
ENTRYPOINT python3 /app/main.py

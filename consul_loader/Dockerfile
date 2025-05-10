FROM python:3.12-slim

WORKDIR /app

COPY /requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY consul_loader/app/consul_loader.py /app/consul_loader.py
COPY consul_loader/config.json /app/config.json

CMD ["python", "/app/consul_loader.py"]


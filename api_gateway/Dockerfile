FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY api_gateway/ /app

ENV PYTHONPATH=/app

CMD ["python", "run.py"]

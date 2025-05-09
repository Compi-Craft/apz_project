FROM python:3.11-slim

WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app directory into the container
COPY auth_service/ /app

ENV PYTHONPATH=/app

CMD ["python", "run.py"]

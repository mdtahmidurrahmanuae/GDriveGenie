FROM python:3.11-slim

WORKDIR /app

COPY webdav/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY webdav/server.py .
COPY config/ /app/config/

CMD ["python", "server.py"]

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends dos2unix && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install -e .

RUN mkdir -p /app/data/synthetic

# Fix Windows line endings
RUN dos2unix start.sh && chmod +x start.sh

EXPOSE 8000

CMD ["bash", "start.sh"]

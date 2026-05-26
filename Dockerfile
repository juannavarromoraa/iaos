FROM python:3.11-slim

# System deps for PDF / scientific stack
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libxml2-dev libxslt1-dev \
        curl ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# default: open a shell; CI/users override with the script they need
CMD ["bash"]

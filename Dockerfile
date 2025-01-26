FROM python:3.11

WORKDIR /app

RUN pip install --upgrade pip

RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini .
COPY wait-for-it.sh .
RUN chmod +x wait-for-it.sh

COPY . .

CMD ["sh", "-c", "./wait-for-it.sh db:5432 -- alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]

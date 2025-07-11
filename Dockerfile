FROM python:3.12-alpine3.21 as builder

WORKDIR /app

RUN pip install --upgrade pip

COPY requirements.txt .

RUN pip wheel --no-cache-dir --wheel-dir /app/wheels .

FROM python:3.12-alpine3.21

WORKDIR /app

COPY --from=builder /app/wheels /app/wheels

RUN pip install --no-cache /app/wheels/*

COPY . .

CMD ["python", "-u", "hyponcloud2mqtt/main.py"]

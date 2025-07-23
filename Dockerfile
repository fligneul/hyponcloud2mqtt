FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends binutils

COPY requirements.txt .
RUN pip install --user -r requirements.txt pyinstaller --no-warn-script-location

COPY src/hyponcloud2mqtt/ /app/hyponcloud2mqtt
WORKDIR /app
RUN /root/.local/bin/pyinstaller --collect-all tzdata --onefile /app/hyponcloud2mqtt/__main__.py -n hyponcloud2mqtt

FROM ubuntu:noble AS runner
RUN apt update && apt install tzdata -y && apt clean && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/dist/hyponcloud2mqtt /app/

WORKDIR /app
CMD ["./hyponcloud2mqtt"]
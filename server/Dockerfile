# Server dati della mappa funghi: scarica i dati con gli stessi script delle Actions,
# tiene l'archivio e il database DuckDB, e pubblica l'uscita su GitHub (che la mette su Pages).
FROM python:3.12-slim

ARG SUPERCRONIC_VERSION=v0.2.33
ARG TARGETARCH

RUN apt-get update \
 && apt-get install -y --no-install-recommends git openssh-client ca-certificates curl tzdata \
 && rm -rf /var/lib/apt/lists/* \
 && arch="${TARGETARCH:-$(dpkg --print-architecture)}" \
 && curl -fsSL -o /usr/local/bin/supercronic \
      "https://github.com/aptible/supercronic/releases/download/${SUPERCRONIC_VERSION}/supercronic-linux-${arch}" \
 && chmod +x /usr/local/bin/supercronic

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY giro.sh avvio.sh db.py crontab /app/
RUN chmod +x /app/giro.sh /app/avvio.sh

ENV TZ=Europe/Rome \
    REPO_DIR=/repo \
    DATI_DIR=/dati \
    PYTHONUNBUFFERED=1

ENTRYPOINT ["/app/avvio.sh"]
CMD ["supercronic", "-passthrough-logs", "/app/crontab"]

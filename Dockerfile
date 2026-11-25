# Optional experimental deployment for Intel/AMD and ARM64 NAS / Raspberry Pi hosts.
# Official LG CLI ARM64 hardware compatibility has not been confirmed.
FROM node:22-bookworm-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 ca-certificates openssh-client tzdata \
 && rm -rf /var/lib/apt/lists/* \
 && npm install -g @webos-tools/cli \
 && useradd --uid 10001 --user-group --home-dir /data --shell /usr/sbin/nologin nuvio \
 && mkdir -p /data /app \
 && chown -R nuvio:nuvio /data
WORKDIR /app
COPY --chown=nuvio:nuvio nuvio/ ./nuvio/
COPY --chown=nuvio:nuvio web/ ./web/
USER nuvio
ENV HOME=/data NUVIO_HOME=/data PYTHONDONTWRITEBYTECODE=1 TZ=Europe/Rome
EXPOSE 8765
VOLUME ["/data"]
CMD ["python3", "-m", "nuvio.server", "serve"]

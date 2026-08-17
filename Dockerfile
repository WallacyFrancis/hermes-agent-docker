FROM nousresearch/hermes-agent:latest

  USER root

  RUN apt-get update \
      && apt-get install -y --no-install-recommends \
          gh \
          chromium \
          ca-certificates \
          fonts-liberation \
          libnss3 \
          libatk-bridge2.0-0 \
          libgtk-3-0 \
          libgbm1 \
          libasound2 \
          libxss1 \
          libxshmfence1 \
      && rm -rf /var/lib/apt/lists/*

  COPY bin/cursor-agent /usr/local/bin/agent
  RUN chmod 0755 /usr/local/bin/agent

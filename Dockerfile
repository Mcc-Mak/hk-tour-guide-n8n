FROM node:24-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 python3-pip python3-venv git wget ca-certificates \
        build-essential && \
    rm -rf /var/lib/apt/lists/* && \
    wget -qO- https://github.com/cli/cli/releases/download/v2.44.1/gh_2.44.1_linux_amd64.tar.gz | tar xz && \
    mv gh_2.44.1_linux_amd64/bin/gh /usr/local/bin/gh && \
    rm -rf gh_2.44.1_linux_amd64 && \
    npm install -g n8n@latest

COPY codebase/.crewai/requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

WORKDIR /data

EXPOSE 5678

CMD ["n8n", "start"]
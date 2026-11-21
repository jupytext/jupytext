FROM mcr.microsoft.com/devcontainers/base:trixie

ARG PIXI_VERSION=v0.84.2

RUN apt-get update \
    && apt-get install -y --no-install-recommends gh \
    && rm -rf /var/lib/apt/lists/* \
    && gh --version

RUN curl -L -o /usr/local/bin/pixi -fsSL --compressed \
    "https://github.com/prefix-dev/pixi/releases/download/${PIXI_VERSION}/pixi-$(uname -m)-unknown-linux-musl" \
    && chmod +x /usr/local/bin/pixi \
    && pixi --version

USER vscode

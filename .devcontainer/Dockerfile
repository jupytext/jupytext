FROM mcr.microsoft.com/devcontainers/base:trixie

ARG PIXI_VERSION=v0.76.1

RUN curl -L -o /usr/local/bin/pixi -fsSL --compressed \
    "https://github.com/prefix-dev/pixi/releases/download/${PIXI_VERSION}/pixi-$(uname -m)-unknown-linux-musl" \
    && chmod +x /usr/local/bin/pixi \
    && pixi --version

USER vscode

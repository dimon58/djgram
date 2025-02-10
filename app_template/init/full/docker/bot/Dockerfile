# syntax = docker/dockerfile:1
# This Dockerfile uses multi-stage build to customize DEV and PROD images:
# https://docs.docker.com/develop/develop-images/multistage-build/

ARG PYTHON_VERSION=3.12.9

FROM python:${PYTHON_VERSION}-slim-bookworm AS development_build

# TODO:
LABEL maintainer=""
LABEL vendor=""
LABEL name=""
LABEL version=""

# Needed for fixing permissions of files created by Docker:
ARG UID=1000
ARG GID=1000

ENV DEBIAN_FRONTEND=noninteractive \
  # python:
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PYTHONDONTWRITEBYTECODE=1 \
  # pip:
  PIP_NO_CACHE_DIR=1 \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  PIP_DEFAULT_TIMEOUT=100 \
  PIP_ROOT_USER_ACTION=ignore \
  PIP_CONSTRAINT='/var/cache/pip_constraint.txt' \
  # tini:
  TINI_VERSION=v0.19.0 \
  # uv:
  UV_VERSION=0.5.29 \
  UV_CACHE_DIR='/root/.cache/uv' \
  UV_PROJECT_ENVIRONMENT='/venv' \
  UV_COMPILE_BYTECODE=1 \
  UV_LINK_MODE=copy \
  # locale:
  LANG=ru_RU.UTF-8 \
  LANGUAGE=ru_RU:ru \
  LC_LANG=ru_RU.UTF-8 \
  LC_ALL=ru_RU.UTF-8

SHELL ["/bin/bash", "-eo", "pipefail", "-c"]


# System deps (we don't use exact versions because it is hard to update them,
# pin when needed):
# gcc для компиляции zstd и typed-ast
# git для уставновки библиотеки python с гитхаба
# graphviz для рисования диаграм диалогов
# locales для отображения русских названий месяцев в datetime
# wget для установки pip
# hadolint ignore=DL3008
RUN apt-get update && apt-get upgrade -y \
  && apt-get install --no-install-recommends -y \
    bash \
    brotli \
    build-essential \
    curl \
    gettext \
    git \
    libpq-dev \
    wait-for-it \
    graphviz \
    locales \
    wget \
  # Installing `tini` utility:
  # https://github.com/krallin/tini
  # Get architecture to download appropriate tini release:
  # See https://github.com/wemake-services/wemake-django-template/issues/1725
  && dpkgArch="$(dpkg --print-architecture | awk -F- '{ print $NF }')" \
  && curl -o /usr/local/bin/tini -sSLO "https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini-${dpkgArch}" \
  && chmod +x /usr/local/bin/tini && tini --version \
  # Installing `uv` package manager:
  # https://docs.astral.sh/uv/guides/integration/docker/#installing-uv \
  && curl -LsSf https://astral.sh/uv/${UV_VERSION}/install.sh | sh \
  && source $HOME/.local/bin/env \
  && uv --version \
  # Setup locale: \
  && sed -i -e 's/# ru_RU.UTF-8 UTF-8/ru_RU.UTF-8 UTF-8/' /etc/locale.gen \
  && locale-gen \
  # Cleaning cache:
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Make uv avaliable
ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /code

RUN groupadd -g "${GID}" -r web \
  && useradd -d '/code' -g web -l -r -u "${UID}" web \
  && chown web:web -R '/code'

# Copy only requirements, to cache them in docker layer:
COPY --chown=web:web ./uv.lock ./pyproject.toml /code/
COPY --chown=web:web ./djgram/pyproject.toml /code/djgram/

# Project initialization:

# `BOT_ENV` arg is used to make prod / dev builds:
ARG BOT_ENV

# Install dependencies
# hadolint ignore=SC2046
RUN --mount=type=cache,target="$UV_CACHE_DIR" \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=djgram/pyproject.toml,target=djgram/pyproject.toml \
    echo "$BOT_ENV" \
    && uv --version \
    && uv sync --frozen --no-install-project --color never \
    $(if [ "$BOT_ENV" = 'production' ]; then echo '--no-dev'; fi)

# This is a special case. We need to run this script as an entry point:
COPY ./docker/bot/entrypoint.sh /docker-entrypoint.sh

# Setting up proper permissions:
RUN chmod +x '/docker-entrypoint.sh' \
  # Replacing line separator CRLF with LF for Windows users:
  && sed -i 's/\r$//g' '/docker-entrypoint.sh'

# Running as non-root user:
USER web

# Place executables in the environment at the front of the path
ENV PATH="$UV_PROJECT_ENVIRONMENT/bin:$PATH"

# We customize how our app is loaded with the custom entrypoint:
ENTRYPOINT ["tini", "--", "/docker-entrypoint.sh"]


# The following stage is only for production:
# https://wemake-django-template.readthedocs.io/en/latest/pages/template/production.html
FROM development_build AS production_build
COPY --chown=web:web . /code

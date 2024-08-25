FROM python:3.12-slim-bullseye as build-python

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y --no-install-recommends graphviz \
  # Cleanup apt cache
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* \

ENV PYTHONFAULTHANDLER=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random
ENV PYTHONDONTWRITEBYTECODE 1
ENV PIP_NO_CACHE_DIR=off
ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PIP_DEFAULT_TIMEOUT=100

# Install Python dependencies
WORKDIR /app

COPY ./djgram/requirements.txt djgram/requirements.txt
RUN pip install --no-cache-dir -r /app/djgram/requirements.txt

COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM build-python as bot

WORKDIR /app
ADD . .

RUN chmod u+x entrypoint.sh

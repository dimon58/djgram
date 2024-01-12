FROM python:3.11-slim-bullseye as build-python

RUN apt-get -y update && apt-get -y upgrade \
  && apt-get -y install graphviz \
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
RUN pip install -r /app/djgram/requirements.txt

COPY ./requirements.txt .
RUN pip install -r requirements.txt

FROM build-python as bot

WORKDIR /app
ADD . .

RUN chmod u+x entrypoint.sh

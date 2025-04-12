# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

FROM debian:bookworm AS libcoap-builder

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update -q \
    && DEBIAN_FRONTEND=noninteractive apt-get install -qy --no-install-recommends \
    autoconf=2.71-* \
    automake=1:1.16.5-* \
    build-essential=12.9* \
    ca-certificates=20* \
    git=1:2.39.5-* \
    libtool=2.4.7-* \
    netbase=6.4 \
    pkg-config=1.8.1-* \
    && rm -rf /var/lib/apt/lists/*

# libcoap
RUN git clone --branch v4.3.5 --depth=1 https://github.com/obgm/libcoap.git

WORKDIR libcoap

RUN ./autogen.sh \
    && ./configure \
    --prefix /opt/libcoap \
    --disable-dtls \
    --disable-documentation \
    --disable-shared \
    && make \
    && make install

FROM python:3.13-slim-bookworm AS poetry-builder

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV POETRY_VERSION=2.1.2
ENV POETRY_VENV=/opt/poetry-venv

RUN python3 -m venv ${POETRY_VENV} \
    && ${POETRY_VENV}/bin/pip install -U pip setuptools \
    && ${POETRY_VENV}/bin/pip install poetry==${POETRY_VERSION}

ENV POETRY=${POETRY_VENV}/bin/poetry

WORKDIR /emfuzzer

COPY . /emfuzzer
RUN ${POETRY} install --no-interaction --no-root
RUN ${POETRY} build --no-interaction
# export freezed requirements
RUN ${POETRY} export --without-hashes --no-interaction > dist/requirements.txt

# final image
FROM python:3.13-slim-bookworm

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV EMFUZZER_VENV=/opt/emfuzzer-venv

RUN python -m venv ${EMFUZZER_VENV}

# apps
RUN apt-get update -q \
    && DEBIAN_FRONTEND=noninteractive apt-get install -qy --no-install-recommends \
    iputils-ping=3:* \
    openssh-client=1:9.2* \
    && rm -rf /var/lib/apt/lists/*

# libcoapp from builder
COPY --from=libcoap-builder /opt/libcoap /opt/libcoap
ENV PATH="/opt/libcoap/bin:$PATH"

# empfuzzer from poetry
WORKDIR /emfuzzer
COPY --from=poetry-builder /emfuzzer/dist /emfuzzer
RUN ${EMFUZZER_VENV}/bin/pip install -r requirements.txt \
  && ${EMFUZZER_VENV}/bin/pip install emfuzzer*.whl \
  && ln -sr ${EMFUZZER_VENV}/bin/emfuzzer /usr/bin

CMD ["emfuzzer"]

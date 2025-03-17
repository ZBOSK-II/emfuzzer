FROM ubuntu:24.04

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update -q \
    && DEBIAN_FRONTEND=noninteractive apt-get install -qy --no-install-recommends \
    ca-certificates=20* \
    git=1:2.43.0-* \
    netbase=6.4 \
    && rm -rf /var/lib/apt/lists/*

# python
RUN apt-get update -q \
    && DEBIAN_FRONTEND=noninteractive apt-get install -qy --no-install-recommends \
    python-is-python3=3.11.4-* \
    python3-venv=3.12.3-* \
    && rm -rf /var/lib/apt/lists/*

# libcoap deps
RUN apt-get update -q \
    && DEBIAN_FRONTEND=noninteractive apt-get install -qy --no-install-recommends \
    build-essential=12.10ubuntu* \
    autoconf=2.71-* \
    automake=1:1.16.5-* \
    build-essential=12.10ubuntu* \
    libtool=2.4.7-* \
    pkg-config=1.8.1-* \
    && rm -rf /var/lib/apt/lists/*

# libcoap
RUN git clone --branch v4.3.5 --depth=1 https://github.com/obgm/libcoap.git \
    && cd libcoap \
    && ./autogen.sh \
    && ./configure \
        --disable-dtls \
        --disable-documentation \
        --disable-shared \
    && make \
    && make install \
    && cd - \
    && rm -r libcoap

# ping
RUN apt-get update -q \
    && DEBIAN_FRONTEND=noninteractive apt-get install -qy --no-install-recommends \
    iputils-ping=3:* \
    && rm -rf /var/lib/apt/lists/*

# venv
RUN python -m venv /opt/venv

RUN echo "#!/bin/bash" > /usr/bin/coapper \
    && echo "PYTHONPATH=/opt /opt/venv/bin/python -m coapper \$@" >> /usr/bin/coapper \
    && chmod +x /usr/bin/coapper

# requirements
COPY requirements.txt /opt/coapper/
RUN /opt/venv/bin/pip install -r /opt/coapper/requirements.txt

# coapper
COPY coapper /opt/coapper

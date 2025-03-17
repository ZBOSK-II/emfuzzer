FROM ubuntu:24.04 as libcoap-builder

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update -q \
    && DEBIAN_FRONTEND=noninteractive apt-get install -qy --no-install-recommends \
    autoconf=2.71-* \
    automake=1:1.16.5-* \
    build-essential=12.10ubuntu* \
    build-essential=12.10ubuntu* \
    ca-certificates=20* \
    git=1:2.43.0-* \
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

FROM ubuntu:24.04

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

COPY --from=libcoap-builder /opt/libcoap /opt/libcoap
ENV PATH="/opt/libcoap/bin:$PATH"

# python
RUN apt-get update -q \
    && DEBIAN_FRONTEND=noninteractive apt-get install -qy --no-install-recommends \
    python-is-python3=3.11.4-* \
    python3-venv=3.12.3-* \
    && rm -rf /var/lib/apt/lists/*

# ping
RUN apt-get update -q \
    && DEBIAN_FRONTEND=noninteractive apt-get install -qy --no-install-recommends \
    iputils-ping=3:* \
    && rm -rf /var/lib/apt/lists/*

# venv
RUN python -m venv /opt/venv

RUN echo "#!/bin/bash" > /usr/bin/coapper \
    && echo "PYTHONPATH=/opt /opt/venv/bin/python -P -m coapper \$@" >> /usr/bin/coapper \
    && chmod +x /usr/bin/coapper

# requirements
COPY requirements.txt /opt/coapper/
RUN /opt/venv/bin/pip install -r /opt/coapper/requirements.txt

# coapper
COPY coapper /opt/coapper
COPY VERSION.tmp /opt/coapper/VERSION

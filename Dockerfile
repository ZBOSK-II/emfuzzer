# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

#
# poetry builder
#
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
RUN ${POETRY} export --no-interaction > dist/requirements.txt

#
# installation base
#
FROM python:3.13-slim-bookworm AS install-base

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# apps
RUN apt-get update -q \
    && DEBIAN_FRONTEND=noninteractive apt-get install -qy --no-install-recommends \
    iputils-ping=3:* \
    openssh-client=1:9.2* \
    && rm -rf /var/lib/apt/lists/*

#
# development image
#
FROM install-base AS emfuzzer-dev

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV POETRY_VENV=/opt/poetry-venv
COPY --from=poetry-builder ${POETRY_VENV}/ /opt/poetry-venv/
ENV POETRY=${POETRY_VENV}/bin/poetry

ENV PATH="${POETRY_VENV}/bin:$PATH"

ADD pyproject.toml .
RUN ${POETRY} install --no-root --no-interaction --with=dev

#
# final image
#
FROM install-base

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV EMFUZZER_VENV=/opt/emfuzzer-venv

RUN python -m venv ${EMFUZZER_VENV}

# empfuzzer from poetry
WORKDIR /emfuzzer
COPY --from=poetry-builder /emfuzzer/dist /emfuzzer
RUN ${EMFUZZER_VENV}/bin/pip install -r requirements.txt \
  && ${EMFUZZER_VENV}/bin/pip install emfuzzer*.whl \
  && ln -sr ${EMFUZZER_VENV}/bin/emfuzzer /usr/bin

CMD ["emfuzzer"]

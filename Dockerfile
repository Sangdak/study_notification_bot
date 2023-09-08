FROM python:3.11

# build dependencies
ARG BUILD_DEPS="curl"
RUN apt-get update && apt-get install -y $BUILD_DEPS

# poetry install
RUN curl -sSL https://install.python-poetry.org | POETRY_VERSION=1.5.0 POETRY_HOME=/root/poetry python3 -
ENV PATH="${PATH}:/root/poetry/bin"

# project initializing
WORKDIR /opt/study_notification_bot

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# instal python libraries via poetry
COPY poetry.lock pyproject.toml /
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

# copying files and dirs to the container.
COPY . .

FROM python:3.10.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    \
    POETRY_VERSION=1.4.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

RUN DEBIAN_FRONTEND=noninteractive apt-get -qq update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    libzbar-dev \
    curl \
    build-essential
RUN pip install "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock ./
RUN poetry export --dev --without-hashes --no-interaction --no-ansi -f requirements.txt -o requirements.txt
RUN pip install -r requirements.txt
COPY . /application
WORKDIR /application
RUN chmod a+x boot.sh
EXPOSE 8000
ENTRYPOINT ["./boot.sh"]

###################################################

# FROM python:3.10.13-slim as base

# FROM base as builder

# ENV PYTHONUNBUFFERED=1 \
#     PYTHONDONTWRITEBYTECODE=1 \
#     \
#     PIP_NO_CACHE_DIR=off \
#     PIP_DISABLE_PIP_VERSION_CHECK=on \
#     PIP_DEFAULT_TIMEOUT=100 \
#     \
#     POETRY_VERSION=1.4.2 \
#     POETRY_HOME="/opt/poetry" \
#     POETRY_VIRTUALENVS_IN_PROJECT=true \
#     POETRY_NO_INTERACTION=1 \
#     \
#     PYSETUP_PATH="/opt/pysetup" \
#     VENV_PATH="/opt/pysetup/.venv"

# RUN DEBIAN_FRONTEND=noninteractive apt-get -qq update && \
#     DEBIAN_FRONTEND=noninteractive apt-get install -y \
#     libzbar-dev \
#     curl \
#     build-essential \
# RUN pip install "poetry==$POETRY_VERSION"

# WORKDIR /src
# COPY pyproject.toml poetry.lock /src/
# RUN poetry export --dev --without-hashes --no-interaction --no-ansi -f requirements.txt -o requirements.txt
# RUN pip install --prefix=/runtime --force-reinstall -r requirements.txt

# COPY . ./src

# FROM base AS runtime
# COPY --from=builder /runtime /usr/local

# COPY . /app
# WORKDIR /app
# RUN chmod a+x boot.sh
# EXPOSE 8000
# ENTRYPOINT ["./boot.sh"]



##########################################""


# FROM python:3.10.13-slim as base

# ENV PYTHONUNBUFFERED=1 \
#     PYTHONDONTWRITEBYTECODE=1 \
#     \
#     PIP_NO_CACHE_DIR=off \
#     PIP_DISABLE_PIP_VERSION_CHECK=on \
#     PIP_DEFAULT_TIMEOUT=100 \
#     \
#     POETRY_VERSION=1.4.2 \
#     POETRY_HOME="/opt/poetry" \
#     POETRY_VIRTUALENVS_IN_PROJECT=true \
#     POETRY_NO_INTERACTION=1 \
#     \
#     PYSETUP_PATH="/opt/pysetup" \
#     VENV_PATH="/opt/pysetup/.venv"

# ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# FROM base as builder

# RUN DEBIAN_FRONTEND=noninteractive apt-get -qq update && \
#     DEBIAN_FRONTEND=noninteractive apt-get install -y \
#     libzbar-dev \
#     curl \
#     build-essential

# # Clean image
# RUN apt-get -yqq clean && \
#     apt-get -yqq purge && \
#     rm -rf /tmp/* /var/tmp/* && \
#     rm -rf /var/lib/apt/lists/*

# RUN curl -sSL https://install.python-poetry.org | python3 -

# WORKDIR $PYSETUP_PATH
# COPY poetry.lock pyproject.toml ./
# RUN poetry install --only main
# RUN poetry run pip install setuptools

# FROM base as runtime
# COPY --from=builder $POETRY_HOME $POETRY_HOME
# COPY --from=builder $PYSETUP_PATH $PYSETUP_PATH

# WORKDIR $PYSETUP_PATH


# COPY cannettes_v2 ./cannettes_v2
# COPY cannettes_configs ./cannettes_configs
# COPY wsgi_v2.py ./wsgi_v2.py
# COPY boot.sh ./boot.sh
# RUN chmod a+x boot.sh
# RUN poetry build

# EXPOSE 8000
# ENTRYPOINT ["./boot.sh"]















# FROM python:3.9.13-slim

# RUN adduser alkivi

# WORKDIR /usr/src/app


# RUN DEBIAN_FRONTEND=noninteractive apt-get -qq update && \
#     DEBIAN_FRONTEND=noninteractive apt-get install -y libzbar-dev

# # Clean image
# RUN apt-get -yqq clean && \
#     apt-get -yqq purge && \
#     rm -rf /tmp/* /var/tmp/* && \
#     rm -rf /var/lib/apt/lists/*


# RUN pip install --upgrade pip
# RUN pip install pipenv 

# COPY Pipfile ./
# COPY Pipfile.lock ./
# RUN pipenv
# RUN pipenv install --system

# #COPY app.py ./
# ADD application ./application
# COPY boot.sh ./boot.sh
# COPY wsgi.py ./wsgi.py
# RUN chmod a+x boot.sh

# RUN chown -R alkivi:alkivi ./
# USER alkivi

# EXPOSE 8000
# ENTRYPOINT ["./boot.sh"]

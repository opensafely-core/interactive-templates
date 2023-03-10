FROM ghcr.io/opensafely-core/python:latest AS python-dev

COPY requirements.unit.txt /root/dev-dependencies.txt
# fix pip-compile so it works by upgrading enough but not too much
RUN --mount=type=cache,target=/root/.cache \
    pip install -U pip pip-tools 'click<8' &&\
    pip install -r /root/dev-dependencies.txt

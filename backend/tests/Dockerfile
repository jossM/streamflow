FROM python:3.9-slim-buster

ENV STREAMFLOW.TEST_MODE="True"

COPY requirements.txt /requirements.txt
COPY api/requirements.txt /requirements_api.txt
COPY requirements_tests.txt /requirements_tests.txt

RUN  pip3 install --upgrade pip \
    && pip3 install -r /requirements.txt \
    && pip3 install -r /requirements_api.txt \
    && pip3 install -r /requirements_tests.txt \
    && pip3 install pipdeptree==2.0.0 \
    && rm -rf ~/.cache
RUN pipdeptree --warn fail

COPY . /streamflow-backend

WORKDIR /streamflow-backend

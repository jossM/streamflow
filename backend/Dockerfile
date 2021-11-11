FROM python:3.9-slim-buster
ARG UID=901
ARG GID=901

#todo
# RUN apt-get update && apt-get install -y procps

COPY requirements.txt /requirements.txt

#todo: switch to poetry
RUN  pip3 install --upgrade pip \
    && pip3 install -r /requirements.txt \
    && pip3 install pipdeptree==2.2.0 \
    && rm -rf ~/.cache
RUN pipdeptree --warn fail

RUN groupadd -g $GID -o streamflow  \
    && useradd -u $UID -g streamflow -m -d /home/streamflow -s /sbin/nologin -c "streamflow user" streamflow
USER streamflow

COPY --chown=streamflow . /streamflow-backend

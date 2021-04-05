FROM python:3.9-slim-buster
ARG API_PORT=5000

RUN groupadd -r streamflow -g 901 && useradd -u 901 -r -g streamflow streamflow

COPY --chown=streamflow . /streamflow-backend

RUN  pip3 install --upgrade pip \
    && pip3 install -r /streamflow-backend/requirements.txt \
    && pip3 install -r /streamflow-backend/api/requirements.txt \
    && rm -rf ~/.cache

RUN pipdeptree --warn fail

USER streamflow

# run api with :
# gunicorn --worker-class gevent --workers 8 --bind 0.0.0.0:$STREAM_FLOW_PORT api.app:app --max-requests 10000 --timeout 5 --keep-alive 5 --log-level info
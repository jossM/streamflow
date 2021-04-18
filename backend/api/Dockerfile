FROM python:3.9-slim-buster

COPY requirements.txt /global-requirements.txt
COPY api/requirements.txt /api-requirements.txt

RUN  pip3 install --upgrade pip \
    && pip3 install -r /global-requirements.txt \
    && pip3 install -r /api-requirements.txt \
    && pip3 install pipdeptree==2.0.0 \
    && rm -rf ~/.cache
RUN pipdeptree --warn fail

USER streamflow

COPY . /streamflow-backend

# run api with :
# gunicorn --worker-class gevent --workers 8 --bind 0.0.0.0:$STREAM_FLOW_PORT api.app:app --max-requests 10000 --timeout 5 --keep-alive 5 --log-level info
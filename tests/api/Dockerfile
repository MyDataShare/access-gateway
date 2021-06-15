# Dockerfile for running API tests
FROM python:3.8-buster

COPY ./requirements.txt ./requirements.txt
COPY ./requirements-dev.txt ./requirements-dev.txt
RUN pip install --no-cache-dir -r ./requirements.txt -r ./requirements-dev.txt

ENV RUN_ENV=test
ENV AGW=http://agw:8199
ENV PYTHONPATH=/app

WORKDIR /app

COPY ./tests/api/run.sh ./tests/api/run.sh
COPY ./tests/api/ ./tests/api/
COPY ./agw ./agw
COPY ./extras ./extras

ENTRYPOINT ["./tests/api/run.sh"]

CMD ["pytest", "-rfxXs", "./tests/api/tests"]

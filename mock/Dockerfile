FROM python:3.8-buster

ENV PYTHONUNBUFFERED=1

RUN mkdir /mock
COPY . /mock
# RUN pip install -r /mock/requirements.txt
ENV MOCK_DP_PORT 1234
ENV MOCK_DP_ROUTES mock_dp.json

WORKDIR /mock
CMD ["sh", "-c", "python3 ./mock_dp.py -p $MOCK_DP_PORT -r $MOCK_DP_ROUTES"]

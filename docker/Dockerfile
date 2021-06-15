FROM python:3.8-buster

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && rm requirements.txt

RUN apt update && apt -y install nginx nginx-extras gettext-base

ARG revision=dev
ENV NGINX_ACCESS_LOG="/dev/stdout request_id"
ENV NGINX_ERROR_LOG="/dev/stderr info"
ENV PYTHONUNBUFFERED=1
ENV GUNICORN_WORKERS=5

WORKDIR /app

RUN echo "$revision" > revision.txt

COPY agw/ ./agw/
COPY docker/run.sh ./docker/run.sh
COPY gateways/ ./gateways/
COPY mock/mock_dp.json ./mock/mock_dp.json
COPY mock/mock_dp.py ./mock/mock_dp.py

# nginx config
COPY docker/nginx.conf /etc/nginx/sites-enabled/default
COPY docker/base-nginx.conf /etc/nginx/nginx.conf

# permissions
RUN groupadd -r agw \
    && useradd --no-log-init -r -g agw agw \
    && chmod -R 750 ./ \
    && chown agw: -R ./ \
    && chown agw: -R /etc/nginx \
    && chown agw: -R /var/lib/nginx \
    && chown agw: -R /var/log/nginx

USER agw

# nginx
EXPOSE 8199

# gunicorn
EXPOSE 8171

ENTRYPOINT ["./docker/run.sh"]

CMD ["gunicorn", "agw:get_app()", "--config", "agw/gunicorn_cfg.py"]

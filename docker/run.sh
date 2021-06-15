#!/usr/bin/env bash
set -o errexit

# Substitute NGINX_ACCESS_LOG in nginx conf with value from  environment variable
envsubst '${NGINX_ACCESS_LOG} ${NGINX_ERROR_LOG}' < /etc/nginx/sites-enabled/default > ./nginx.temp
mv ./nginx.temp /etc/nginx/sites-enabled/default

# Start mock DP if AGW_START_MOCK_DP is true
if [[ $AGW_START_MOCK_DP == "true" ]]; then
    ROUTES="./mock/mock_dp.json"
    if [ "x$AGW_MOCK_DP_ROUTES_FILE" != "x" ]; then
        ROUTES=$AGW_MOCK_DP_ROUTES_FILE
    fi
    echo "AGW_START_MOCK_DP is true, starting mock DP with '$ROUTES'."
    python ./mock/mock_dp.py --port 19190 --routes "$ROUTES" 1> /dev/null &
fi

# Start nginx
nginx

exec "$@"

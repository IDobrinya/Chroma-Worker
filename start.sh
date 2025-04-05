#!/bin/bash
set -e
trap 'echo "Ошибка. Нажмите Enter для выхода..."; read' ERR
[ -f .env ] && export $(grep -v '^#' .env | xargs)
[ -z "$PORT" ] && PORT=80
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
py -m pip install ngrok
if [ -z "$NGROK_AUTHTOKEN" ]; then
    echo "Ошибка: NGROK_AUTHTOKEN не задан."
    exit 1
fi
set +e
ngrok config add-authtoken $NGROK_AUTHTOKEN
set -e
ngrok http $PORT --log=stdout > /dev/null &
sleep 3
PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*' | grep -o 'http[^"]*')
echo "Your server address: $PUBLIC_URL"
py -m app

# TradingAgents Cloud Backend

This folder adds a deployable FastAPI service around `TradingAgentsGraph`.

## Local API

```bash
cd E:\AI\Git\TradingAgents
pip install -e . -r server/requirements.txt
uvicorn server.app.main:app --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

Create a job:

```bash
curl -X POST http://localhost:8000/api/analyses ^
  -H "Content-Type: application/json" ^
  -H "X-API-Key: change-me" ^
  -d "{\"ticker\":\"NVDA\",\"trade_date\":\"2024-05-10\",\"analysts\":[\"market\",\"news\",\"fundamentals\"]}"
```

## Production Docker + Nginx + HTTPS

1. Copy `server/.env.example` to `server/.env`.
2. Fill API keys, `TRADINGAGENTS_API_KEY`, `NGINX_SERVER_NAME`, `CERTBOT_DOMAIN`, and `CERTBOT_EMAIL`.
3. Bootstrap HTTP for Let's Encrypt:

```bash
cd server
NGINX_TEMPLATE=http-only.conf.template docker compose -f docker-compose.prod.yml up -d nginx front api
docker compose -f docker-compose.prod.yml --profile certbot run --rm certbot
```

4. Switch to HTTPS:

```bash
docker compose -f docker-compose.prod.yml down
NGINX_TEMPLATE=https.conf.template docker compose -f docker-compose.prod.yml up -d --build
```

The API is exposed under `/api`, while the Vue frontend is served from `/`.


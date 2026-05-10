# TradingAgents Vue Console

Vue 3 frontend for the FastAPI backend in `server/`.

## Local Development

Start the backend first:

```bash
cd ..
pip install -e . -r server/requirements.txt
uvicorn server.app.main:app --host 0.0.0.0 --port 8000
```

Then start the frontend:

```bash
cd front
npm install
npm run dev
```

The Vite dev server proxies `/api` and `/health` to `http://localhost:8000`.

## Production

The production stack is controlled by `server/docker-compose.prod.yml`.
The frontend image builds this app and serves static files through Nginx.


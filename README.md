# openclaw-search-proxy

Search proxy API for the OpenClaw ecosystem, powered by DuckDuckGo.  
提供给 OpenClaw Skills / Extensions 使用的 DuckDuckGo 代理搜索服务。

## API Overview

All endpoints accept both **GET** and **POST**. Parameters:

- `q` (string, required): search query
- `max_results` (int, optional, default `10`): maximum number of results to return

Base URL examples:

- Local: `http://localhost:8000`
- Vercel / other hosting: `https://<your-domain>`

### New v1 endpoints (recommended for OpenClaw)

- `GET /v1/search/text`
- `GET /v1/search/answers`
- `GET /v1/search/images`
- `GET /v1/search/videos`

Example:

```bash
curl "http://localhost:8000/v1/search/text?q=OpenClaw&max_results=3"
```

Response:

```json
{
  "query": "OpenClaw",
  "type": "text",
  "results": [
    { "title": "...", "href": "...", "body": "..." }
  ]
}
```

### Legacy endpoints (kept for compatibility)

These routes are still available and return the original shape:

- `GET /search`
- `GET /searchAnswers`
- `GET /searchImages`
- `GET /searchVideos`

They respond with:

```json
{ "results": [ /* raw DuckDuckGo results */ ] }
```

## Health check

- `GET /health` → `{"status": "ok"}`
- `GET /` → basic service info and endpoint list

---

## Deploy with Docker

### Run directly

```bash
docker build -t openclaw-search-proxy .
docker run -p 8000:8000 openclaw-search-proxy
```

Then visit:

- `http://localhost:8000/v1/search/text?q=OpenClaw&max_results=3`

### docker-compose

```yaml
version: "3.8"

services:
  openclaw-search-proxy:
    image: openclaw-search-proxy:latest
    build: .
    restart: always
    ports:
      - "8000:8000"
    # environment:
    #   - http_proxy=http://127.0.0.1:7890
    #   - https_proxy=http://127.0.0.1:7890
```

---

## Vercel deployment

You can still deploy on Vercel as a simple HTTP API (note: free plan limits and IP blocking may apply).

1. Fork `OpenClawHQ/openclaw-search-proxy` (this repo).
2. Go to [vercel.com](https://vercel.com/) and log in with GitHub.
3. Click **Import Project** → **Import Git Repository** and select your fork.
4. Keep defaults and click **Deploy**.

After deployment, you can use:

```bash
curl "https://<your-vercel-domain>/v1/search/text?q=OpenClaw&max_results=3"
```

---

## OpenClaw Integration Example (SKILL.md snippet)

You can call this API from an OpenClaw Skill via `curl`:

```markdown
## Commands / Actions

### search-web

Use DuckDuckGo via openclaw-search-proxy to search the web.

```bash
BASE_URL="http://localhost:8000"  # or your deployed URL
QUERY="$1"                        # search query
MAX_RESULTS="${2:-5}"

curl -s "$BASE_URL/v1/search/text" \
  --get \
  --data-urlencode "q=$QUERY" \
  --data-urlencode "max_results=$MAX_RESULTS" \
  | jq '.results'
```
```

You can adapt this pattern into your own `SKILL.md` in any skill repo.

---

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
FLASK_APP=app.py flask run --host 0.0.0.0 --port 8000
```

Or with gunicorn:

```bash
gunicorn -b 0.0.0.0:8000 app:app
```

---

## Acknowledgements

This project is based on and would not exist without:

- [`binjie09/duckduckgo-api`](https://github.com/binjie09/duckduckgo-api)
- [`Jah-yee/duckduckgo-api`](https://github.com/Jah-yee/duckduckgo-api)

Original work is licensed under MIT; this fork stays MIT and adapts it for the OpenClawHQ organization and ecosystem.

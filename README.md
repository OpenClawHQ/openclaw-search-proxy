# openclaw-free-search-proxy

[![CI – Simple tests](https://github.com/OpenClawHQ/free-search-proxy/actions/workflows/simple-tests.yml/badge.svg)](https://github.com/OpenClawHQ/free-search-proxy/actions/workflows/simple-tests.yml)
[![Awesome](https://awesome.re/badge.svg)](https://awesome.re)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)

Search proxy API adapted for the OpenClaw ecosystem, powered by [duckduckgo-api](https://github.com/binjie09/duckduckgo-api).

---

## Overview

`openclaw-free-search-proxy` wraps DuckDuckGo search endpoints behind a small HTTP service that is easy to call from OpenClaw Skills and Extensions.

**Use cases:**

- Web search from within an OpenClaw Skill
- Lightweight “search tool” for agents (text / answers / images / videos)
- Simple HTTP API you can host on Docker or Vercel

**Base URLs:**

- Local: `http://localhost:8000`
- Hosted: `https://<your-domain>`

---

## API

All endpoints accept both **GET** and **POST** and support the same parameters:

- `q` (string, required): search query
- `max_results` (int, optional, default `10`): maximum number of results to return

### v1 endpoints (recommended)

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
  "ok": true,
  "query": "OpenClaw",
  "type": "text",
  "results": [
    { "title": "...", "href": "...", "body": "..." }
  ],
  "meta": {
    "max_results": 3
  }
}
```

### Legacy endpoints (compatibility)

The original routes are still available and return the older shape:

- `GET /search`
- `GET /searchAnswers`
- `GET /searchImages`
- `GET /searchVideos`

They respond with:

```json
{ "results": [ /* raw DuckDuckGo results */ ] }
```

### Health

- `GET /health` → `{"status": "ok"}`
- `GET /` → basic service info and endpoint list

---

## Configuration & auth

You can control behaviour via environment variables:

- `SEARCH_DEFAULT_MAX_RESULTS` (default `10`)
- `SEARCH_MAX_RESULTS_HARD_LIMIT` (default `50`)
- `FREE_SEARCH_PROXY_TOKEN` (optional shared secret; when set, v1 endpoints require `X-OpenClaw-Search-Token` to match)

---

## Deploy with Docker

### Run directly

```bash
docker build -t openclaw-free-search-proxy .
docker run -p 8000:8000 openclaw-free-search-proxy
```

Then visit:

- `http://localhost:8000/v1/search/text?q=OpenClaw&max_results=3`

### docker-compose

```yaml
version: "3.8"

services:
  openclaw-free-search-proxy:
    image: openclaw-free-search-proxy:latest
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

You can deploy this API to Vercel as a simple Python service (note: free plan limits and IP blocking may apply).

1. Fork [`OpenClawHQ/free-search-proxy`](https://github.com/OpenClawHQ/free-search-proxy).
2. Go to [vercel.com](https://vercel.com/) and log in with GitHub.
3. Click **Import Project** → **Import Git Repository** and select your fork.
4. Keep defaults and click **Deploy**.

After deployment, you can use:

```bash
curl "https://<your-vercel-domain>/v1/search/text?q=OpenClaw&max_results=3"
```

---

## OpenClaw integration example (`SKILL.md`)

You can call this API from an OpenClaw Skill via `curl`:

```markdown
## Commands / Actions

### search-web

Use DuckDuckGo via openclaw-free-search-proxy to search the web.

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

Original work is licensed under MIT; this fork stays MIT and adapts it for the OpenClawHQ organization and ecosystem.

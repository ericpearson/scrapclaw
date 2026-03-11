# scrapclaw

Standalone containerized Scrapling API service, based on the working `../vpn/scrapling-api` project.

## What it does

This service exposes:

- `GET /health` for container health checks
- `POST /v1` for Scrapling-backed page fetches with Cloudflare solving enabled

The API shape matches the existing service so it can be dropped in as a replacement.

## Run with Docker Compose

```bash
docker compose up --build
```

The service listens on `http://localhost:8192`.

## Run with Docker

```bash
docker build -t scrapclaw .
docker run --rm -p 8192:8192 scrapclaw
```

## Example request

```bash
curl -X POST http://localhost:8192/v1 \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com","maxTimeout":60000,"wait":0}'
```

## GitHub Container Registry

The repository includes a GitHub Actions workflow that builds the image on pushes and publishes `ghcr.io/ericpearson/scrapclaw:latest` from the `main` branch.

For that to work, the repository's Actions permissions need `packages: write`.

# scrapclaw

Standalone containerized Scrapling API service, based on the working `../vpn/scrapling-api` project.

It exposes a small FastAPI app that uses `scrapling`'s `StealthyFetcher` with Cloudflare solving enabled, packaged as a Docker image that can be run locally or published to GitHub Container Registry.

## Features

- `GET /` basic service status
- `GET /health` health check endpoint for Docker and load balancers
- `POST /v1` Scrapling-backed page fetch endpoint
- Dockerfile ready for local builds and container platforms
- `docker-compose.yml` for local or server deployment
- GitHub Actions workflow to build and publish `ghcr.io/ericpearson/scrapclaw`

## Project files

- `main.py`: FastAPI app and `/v1` implementation
- `Dockerfile`: image build based on `ghcr.io/d4vinci/scrapling:latest`
- `docker-compose.yml`: local deployment config with health check
- `.github/workflows/docker.yml`: build and publish workflow for GitHub Actions

## Requirements

- Docker with Compose support
- Optional: a GitHub repository with Actions enabled if you want automated image publishing

## Local development

### Build and run with Docker Compose

```bash
docker compose up --build
```

The API will be available at `http://localhost:8192`.

### Build and run with plain Docker

```bash
docker build -t scrapclaw .
docker run --rm -p 8192:8192 scrapclaw
```

### Stop the service

```bash
docker compose down
```

## API

### Health check

```bash
curl http://localhost:8192/health
```

Expected response:

```json
{"status":"ok"}
```

### Fetch a page

```bash
curl -X POST http://localhost:8192/v1 \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com","maxTimeout":60000,"wait":0}'
```

Request body:

- `url`: target URL to fetch
- `maxTimeout`: request timeout in milliseconds
- `wait`: extra wait time in milliseconds after navigation
- `cmd`: accepted for compatibility, defaults to `request.get`

Response shape:

```json
{
  "status": "ok",
  "message": "",
  "startTimestamp": 0,
  "endTimestamp": 0,
  "solution": {
    "url": "https://example.com",
    "status": 200,
    "response": "<html>...</html>",
    "cookies": [],
    "userAgent": ""
  }
}
```

On failure the service returns:

```json
{
  "status": "error",
  "message": "error text",
  "startTimestamp": 0,
  "endTimestamp": 0,
  "solution": {}
}
```

## Configuration

The container supports:

- `PORT`: HTTP listen port inside the container. Defaults to `8192`.
- `TZ`: timezone. The compose file currently uses `America/Toronto`.

If you want to change the exposed host port in `docker-compose.yml`, update both the `ports` mapping and the `PORT` environment value together.

## Deployment

### Deploy with Docker Compose on a server

```bash
docker compose pull
docker compose up -d --build
```

### Deploy from GHCR

If GitHub Actions is publishing your image, you can replace the `build:` section in `docker-compose.yml` with:

```yaml
image: ghcr.io/ericpearson/scrapclaw:latest
```

Then deploy with:

```bash
docker compose pull
docker compose up -d
```

### Deploy in Portainer

Use the compose file in this repo as the stack definition. If you're using a published GHCR image, point the service at `ghcr.io/ericpearson/scrapclaw:latest` instead of building locally.

## GitHub Actions and GHCR

The workflow in `.github/workflows/docker.yml`:

- builds on pull requests
- builds and pushes on `main`
- builds and pushes on version tags like `v1.0.0`

For publishing to work:

- the repository needs Actions enabled
- Actions permissions need `packages: write`
- the package visibility in GHCR should be set the way you want for deployment

## Notes

- This repo is intentionally minimal and mirrors the behavior of the existing `../vpn/scrapling-api` service.
- `scrapling install` runs during image build so the browser automation pieces are available in the final container.

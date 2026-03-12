# scrapclaw

Standalone containerized Scrapling API service for browser-backed page fetches, including Cloudflare-protected targets.

It exposes a small FastAPI app that uses `scrapling`'s `StealthyFetcher` with Cloudflare solving enabled, packaged as a Docker image that can be run locally or published to GitHub Container Registry.

## Features

- `GET /` basic service status
- `GET /health` health check endpoint for Docker and load balancers
- `POST /v1` Scrapling-backed page fetch endpoint
- Default blocking for localhost, private LAN, link-local, and other non-public targets
- Optional bearer-token auth for API clients
- Dockerfile ready for local builds and container platforms
- `docker-compose.yml` for local or server deployment
- OpenClaw-compatible skill bundle in `skills/scrapclaw`
- GitHub Actions workflow to build and publish `ghcr.io/ericpearson/scrapclaw`

## Project files

- `main.py`: FastAPI app and `/v1` implementation
- `Dockerfile`: image build based on `ghcr.io/d4vinci/scrapling:latest`
- `docker-compose.yml`: local deployment config with health check
- `skills/scrapclaw/SKILL.md`: OpenClaw skill that teaches an agent how to call the API
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
- `SCRAPCLAW_BLOCK_PRIVATE_NETWORKS`: block requests to localhost/private/link-local targets. Defaults to `true`.
- `SCRAPCLAW_ALLOWED_HOSTS`: comma-separated hostname allowlist that bypasses private-network blocking.
- `SCRAPCLAW_API_TOKEN`: optional bearer token required on `POST /v1` when set.
- `SCRAPCLAW_MAX_TIMEOUT_MS`: upper bound for `maxTimeout`. Defaults to `120000`.
- `SCRAPCLAW_MAX_WAIT_MS`: upper bound for `wait`. Defaults to `10000`.

If you want to change the exposed host port in `docker-compose.yml`, update both the `ports` mapping and the `PORT` environment value together.

### Security defaults

`POST /v1` only accepts `http` and `https` URLs and only supports `cmd: "request.get"`.

By default, Scrapclaw resolves the target hostname and rejects requests that land on:

- loopback addresses
- RFC1918/private ranges
- link-local addresses
- multicast, reserved, and unspecified ranges

If you intentionally need an internal hostname, add it to `SCRAPCLAW_ALLOWED_HOSTS`.

If `SCRAPCLAW_API_TOKEN` is set, clients must send:

```bash
-H "Authorization: Bearer $SCRAPCLAW_API_TOKEN"
```

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

## OpenClaw

OpenClaw workspace skills live in `<workspace>/skills`, and each skill is a folder containing a `SKILL.md`. This repo includes a ready-to-install skill bundle at `skills/scrapclaw`, paired with a published Docker image so agents have a browser-backed fetch service to call.

### Recommended install path

Run the published container image first:

```bash
docker run --rm -d \
  --name scrapclaw \
  -p 8192:8192 \
  ghcr.io/ericpearson/scrapclaw:v0.0.2
```

That same image is the intended runtime for the GitHub `v0.0.2` release.

If you use the source-build path instead, review the repo, [Dockerfile](/Users/epearson/projects/scrapclaw/Dockerfile), and [docker-compose.yml](/Users/epearson/projects/scrapclaw/docker-compose.yml) before running `docker compose up --build -d`. Building unreviewed code can execute arbitrary commands on the host.

Then install the skill from ClawHub:

```bash
clawhub install scrapclaw --version 0.0.2
```

If you prefer to run from source, you can still use:

```bash
git clone https://github.com/ericpearson/scrapclaw.git
cd scrapclaw
docker compose up --build -d
```

For local installs, expect to need `docker`, `docker compose`, `git`, and `curl`.

### Install the local skill into an OpenClaw workspace

```bash
mkdir -p ~/.openclaw/workspace/skills
cp -R skills/scrapclaw ~/.openclaw/workspace/skills/
```

OpenClaw will pick it up in the next session, or after a skills refresh.

### Optional: point the skill at a non-default Scrapclaw URL

By default the skill assumes Scrapclaw is reachable at `http://127.0.0.1:8192`. To override that, set `SCRAPCLAW_BASE_URL` in your OpenClaw skill config:

```json5
{
  skills: {
    entries: {
      scrapclaw: {
        env: {
          SCRAPCLAW_BASE_URL: "https://scrapclaw.example.com"
        }
      }
    }
  }
}
```

If you configure `SCRAPCLAW_API_TOKEN` on the service, also provide it to the skill environment so the bundled `curl` command sends the bearer token.

### Publish the skill to ClawHub

OpenClaw's ClawHub registry publishes versioned skill folders, not the whole repo. Publish the bundled skill directory like this:

```bash
clawhub publish ./skills/scrapclaw \
  --slug scrapclaw \
  --name "Scrapclaw" \
  --version 0.0.2 \
  --changelog "Release 0.0.2" \
  --tags latest
```

After that, OpenClaw users can install it with:

```bash
clawhub install scrapclaw --version 0.0.2
```

## GitHub Actions and GHCR

The workflow in `.github/workflows/docker.yml`:

- builds on pull requests
- builds and pushes on `main`
- builds and pushes on version tags like `v1.0.0`

To publish a container release from this repo, push a semver tag such as `v0.0.2`.

For publishing to work:

- the repository needs Actions enabled
- Actions permissions need `packages: write`
- the package visibility in GHCR should be set the way you want for deployment

## Notes

- This repo is intentionally minimal and focuses on exposing Scrapling through a small HTTP API plus an OpenClaw skill wrapper.
- `scrapling install` runs during image build so the browser automation pieces are available in the final container.

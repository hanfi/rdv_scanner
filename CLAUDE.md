# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Create the environment and install Python/browser dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# Local configuration; set PAGE_1_URL through PAGE_N_URL and GEMINI_API_KEY in .env
cp .env.example .env

# Run one scan or the continuous scanner (continuous is the default)
python scanner.py --once
python scanner.py --continuous

# Build and run the container
# The scanner expects its runtime environment variables to be configured.
docker build -t rdv-scanner .
docker run --rm -p 8080:8080 -p 8081:8081 --env-file .env rdv-scanner

# Standalone health endpoint smoke check (runs for 60 seconds)
python health_check.py
# While it is running, in another terminal:
curl http://localhost:8080/health
```

There is no configured lint command or automated test suite, so there is no supported single-test command. `test_quota_optimization.py` is an obsolete standalone script, not a pytest suite: it refers to absent quota/scanner modules and writes `MIGRATION_GUIDE.md`. `TEST_LOCAL.md` references a missing `test_cloud_mode.sh`.

## Architecture

`scanner.py` is the runtime entrypoint and owns the Playwright lifecycle. It loads `.env`, reads consecutive `PAGE_1_URL` through `PAGE_N_URL` settings, scans each configured page sequentially in one Chromium session, captures captcha and page screenshots under `screenshots/`, retries each page up to three times, and classifies whether appointment slots are available. `--once` runs one scan cycle; continuous mode repeats after `CHECK_INTERVAL` and starts the HTTP services.

Captcha strategy is split across the solver modules. `hybrid_optimized_solver_clean.py` orchestrates multimodal image+audio, image-only, and audio-only fallbacks. `multimodal_gemini_solver.py` handles Gemini model candidates, rate-limit fallback, and optional `GEMINI_MODEL_PRIORITY` / `GEMINI_MULTIMODAL_MODELS` configuration. `gemini_solver.py` implements the image-only fallback. The scanner passes successful availability results to `notifier.py`, which posts a Slack-compatible webhook payload when `NOTIFICATION_WEBHOOK` is set; otherwise it logs the notification.

In continuous mode, `health_check.py` serves a static `/health` response on port 8080, while `screenshot_viewer_secure.py` serves the screenshot UI, listing/download/cleanup routes, and its own public health route on port 8081. The viewer requires `SCREENSHOT_TOKEN` or configured Basic Auth for non-health routes and generates/logs a token if none is set. `screenshot_viewer.py` is an older, unused alternative; the scanner imports the secure viewer.

## Configuration and deployment notes

Use `.env.example` as the local template. The code reads consecutive `PAGE_1_URL` through `PAGE_N_URL` settings, `GEMINI_API_KEY`, `HEADLESS`, `MUTE_BROWSER`, `BACKGROUND_MODE`, `CHECK_INTERVAL`, and optional notification/viewer settings. In continuous mode the viewer listens on `$PORT` (set by Railway), else `SCREENSHOT_PORT`, else 8081; the separate health server uses `HEALTH_PORT` (default 8080) and is skipped if it would collide with the viewer port, since the viewer also serves `/health`. `ENABLE_HEALTH_CHECK` is not read. The health endpoint reports that the service is healthy but does not inspect scanner state.

Deployment: `railway.json` uses the `DOCKERFILE` builder, because `/start.sh` and the Xvfb/fluxbox/`x11-utils` setup exist only in the Docker image; its health check hits `/health` on `$PORT`, which the viewer serves. `start.sh` defaults `XVFB_WHD` to `1366x768x24`. `.dockerignore` keeps `.env`, `.venv/`, and generated screenshots out of the image; runtime variables are configured in Railway, not baked in.

The README contains stale setup and feature claims. In particular, copy `.env.example` (not `.env`) to create local configuration; the notifier uses `NOTIFICATION_WEBHOOK` rather than the documented Slack bot variables, and email settings are not implemented. Check the Python modules and deployment files when documentation disagrees with runtime behavior.

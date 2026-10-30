# Deploy and configure

## Run locally

```bash
uv sync
cp .env.example .env        # add your Google AI Studio key
uv run --env-file .env uvicorn app.main:app --reload
```

Open http://localhost:8000. With no key, only the recorded samples play. `MOCK=1` runs the whole loop with a placeholder
attacker, offline. Self-checks: `uv run python -m app.meta`, `app.agent`, `app.pipeline`, `app.regions.india`,
`app.regions.us` and `app.telegram_bot --selftest`.

## Deploy on Render

[render.yaml](../render.yaml) describes a free Docker web service. The image builds and runs on Render.

1. In Render choose **New, then Blueprint**, pick the repo and the `main` branch.
2. Fill in the two secrets: `OPEN_API_KEY` (your Google AI Studio key) and `LIVE_CODE` (an access code you choose).
3. Apply, and wait for the build. Open `/api/status`: it should show `"live": true`, the model name and `"code": true`.

Every push to `main` rebuilds the site. The free plan sleeps after about 15 minutes idle, and the first visit then takes
about a minute, so open the link a few minutes before presenting. To change a setting later, edit it in the service's
Environment tab; Render redeploys.

## Settings

| Setting | What it does | Default |
|---|---|---|
| `OPEN_API_KEY` | The model's API key. Without it only samples play. | none |
| `OPEN_API_BASE` | An OpenAI-compatible endpoint | Google's Gemini endpoint |
| `OPEN_MODEL` | Which model finds the clues | `gemini-3-flash-preview` |
| `OPEN_LABEL`, `OPEN_HOST` | Names the page shows for the model and its host | Gemini 3 Flash, Google AI Studio |
| `OPEN_RPM` | Our own requests per minute for that model, so a free key does not answer 429 | `4` on the free tier |
| `OPEN_RECHECK_MODEL`, `OPEN_RECHECK_RPM` | A different model for the re-attacks. Off; the one we tried did not work | empty |
| `LIVE_CODE` | When set, live runs need this code. The samples never do. | empty (open) |
| `RUNS_PER_HOUR`, `RUNS_PER_DAY` | Live runs allowed per visitor and per site | 2 and 6 in `render.yaml` |
| `REGION` | Country packs to load: `in`, `us`, comma separated, or `global` for none | `in` |
| `BOX_SNAP`, `BOX_FOCUS` | Box tightening, see [how-it-works.md](how-it-works.md) | on, `object` |
| `TELEGRAM_BOT_TOKEN`, `BOT_RUNS_PER_HOUR` | For the Telegram bot | none, 3 |

## Quotas

The free Gemini tier allows 20 requests a day per model per project, and 5 a minute, which is about three or four
checks. A public demo should therefore rely on the recorded samples, or the project should have billing turned on. See
[models.md](models.md).

## Access code

The code is one shared secret, with no lockout after wrong guesses, so use a long random string for anything public.
Run limits cap the damage of a leak. Never put a key or the code in a file that is committed; `.env` is git-ignored.

## Telegram bot

[app/telegram_bot.py](../app/telegram_bot.py) puts the same agent behind a Telegram chat.

1. In Telegram, talk to **@BotFather**, send `/newbot`, and copy the token.
2. Put it in `.env` as `TELEGRAM_BOT_TOKEN=...`.
3. Run `uv run --env-file .env python -m app.telegram_bot` and keep the window open.
4. In the chat send `/unlock <access code>` (the same `LIVE_CODE`), then a photo. `/lang en|te|hi` sets the report language.

It is a separate process from the website, so run it on a laptop for a demo. One photo is checked at a time. It has passed
an offline self-check against a fake Telegram but has not been run against the real service yet.

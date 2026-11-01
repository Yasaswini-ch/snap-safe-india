# Contributing to Snap Safe India

Thanks for helping. This is a small project, so the rules are short.

## Ground rules

- **Only made-up data.** Never put a real ID, number plate, phone number, address or photo of a person in the repository, an issue or a
  test. Test images carry fictional values. If you are unsure, it is real: leave it out.
- **No keys in git.** API keys, tokens and access codes go in `.env` (git-ignored) or the host's secret settings, never in a file.
- **Be honest about results.** If you change detection or edits, say what you measured and how many runs. One run on generated scenes
  shows a change helps in that case, not that it always does. `docs/benchmark.md` shows the style.

## Good first contributions

- **A region pack** for another country: one file in `app/regions` with its ID patterns, address words and prompt note. Start from
  `docs/adding-a-country.md` and keep the pack's self-check passing.
- **More languages** for the reports and the "talk the checker out of reporting" phrases in `app/meta.py`. Have a native reader check them.
- **Tighter boxes or a better fill** in `app/pipeline.py`: the largest known weakness is boxes that are bigger than the text.
- **Another open model.** Anything OpenAI-compatible with image input works through `OPEN_API_BASE` and `OPEN_MODEL`. Gemma 4 and Gemini 3
  Flash are the only ones tested; run `python -m bench.indiabench` with yours and send the numbers.

## Running the checks

```bash
uv sync
uv run python -m app.meta
uv run python -m app.agent
uv run python -m app.pipeline
uv run python -m app.regions.india
uv run python -m app.telegram_bot --selftest
uv run python -m tests.test_language
uv run python -m tests.test_requestcount
uv run python -m tests.test_keypool
uv run python -m tests.test_whatsapp
```

They run offline, with no key and no quota. Run them before you open a pull request, and keep the pull request to one change.

## Where things are

`README.md` has the overview and `docs/` has the details: how the agent works, models and quotas, the benchmark, deployment, the Telegram
and WhatsApp bots. `skills/snap-safe-india/SKILL.md` explains how another AI agent can call the tool.

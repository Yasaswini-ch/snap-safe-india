# Snap Safe India: who does what

The team plan for Hacktoberfest Hack Day x AI for Vizag (Sunday, Nov 1, 2026, 10:00 AM to 5:00 PM IST; submission window 3:45 to 4:15 PM, demos from 4:15 PM). This file mirrors the plan page and is updated by hand, so check the task cards against what is actually done. The access code and the API keys are shared privately and are never written in the repo.

- Code: https://github.com/Yasaswini-ch/snap-safe-india
- Live site: https://snap-safe-india.onrender.com

## Where we are

### Done

- The agent: finds clues, plans the fewest edits, edits, re-checks
- India detection: Aadhaar (with checksum), PAN, plates, UPI, PIN codes, Telugu and Hindi notes
- Region packs, so other countries are one file each
- Indian benchmark: 10 rendered scenes defined, 5 core scenes run by default, and a scorer
- New page, logo, README, Render config
- Pushed to GitHub with a clean history
- Deployed on Render and answering, with the access code switched on
- Report language: English, Telugu or Hindi
- Three samples recorded (ID card, parcel label, Telugu sign), each checked by reading the cleaned photo: nothing readable
- Telegram bot, written and tested offline
- The live page, tested by the team: no problems found

### Blocked

- Gemini 3 Flash is the fast, accurate model. Its free tier gives **20 requests a day per Google project**. The new key has used most of today's. The old key resets around 12:30 PM IST.
- Two samples are left (number plate, UPI screen), about 8 requests. The five-scene benchmark needs about 20 Gemini requests per run, two runs.
- Fix: switch on billing for the Google AI Studio project, or record only two samples after the reset.

### Not tested yet

- The Telegram bot against real Telegram (it needs a token)
- A full live check on the deployed site (it needs the new Google key in Render's settings)
- Real phone photos instead of rendered scenes

## Task lists

Estimates are rough. Swap tasks if someone is faster at something. Yasaswini keeps the Google key and the Render account, adds both of you as collaborators, and answers questions.

### Likhitha: Setup, samples and backend

- [ ] **Set up the project on a laptop** (30 min)
  - Install Git and uv. Clone `https://github.com/Yasaswini-ch/snap-safe-india.git`, run `uv sync`, copy `.env.example` to `.env` and put the Google key in it. Get the key from Yasaswini in a private message, and never commit `.env`. Then run `uv run python -m app.meta`; it should print `meta ok`.
  - **Needs:** an invite to the GitHub repo, and the key
  - **Done when:** the self-checks pass and `uv run --env-file .env uvicorn app.main:app` opens the page at localhost:8000.
- [ ] **Run one live check on the live site** (20 min)
  - The page, its status and the samples were tested and no problems were found. What is left is one real check: open the Render link, type the access code, choose English, upload `id_card.jpg` from `bench/india/images` in the repo, and wait 1 to 3 minutes. It only works once Yasaswini has put the new Google key into Render's `OPEN_API_KEY`, and while Gemini quota is left.
  - **Needs:** the access code and the new key on Render, from Yasaswini
  - **Done when:** the check finishes, or the exact error message is sent to Yasaswini.
- [ ] **Real phone photos** (1 h)
  - Make 4 or 5 props with made-up values only: an ID-style card, a parcel label, a house name board, a number plate on paper. Photograph them with a phone, with an angle and some glare. Never use a real document or a real number.
  - **Needs:** nothing, start now
  - **Done when:** the photos are in one folder, ready for a live test.
- [ ] **Record the two missing samples** (30 min)
  - The ID card, parcel label and Telugu sign are recorded. Record the rest one at a time: `uv run --env-file .env python -m app.samples in_plate`, then `in_upi`. Each uses about 4 Gemini requests. Play each at localhost:8000 and check the cleaned photo shows no readable value (a few extra pixelated blocks are fine). Run `git pull`, then commit `static/samples` and push. Do this before the benchmark starts, because everyone using the key shares Gemini's per-minute limit.
  - **Needs:** the setup, and Gemini quota (a new day, or billing)
  - **Done when:** five samples show in “Watch a sample”.
- [ ] **QA pass** (1 h)
  - On a laptop and a phone: click every sample, type in the caption box, upload one scene from `bench/india/images` as a live check, try dark mode and a narrow window. Write each bug as page, steps, screenshot.
  - **Needs:** the samples recorded
  - **Done when:** the bug list exists: page bugs go to Sriya, backend bugs stay with Likhitha, and fixed bugs are re-checked.
- [ ] **Fix the backend bugs from QA** (ongoing)
  - Fix the backend bugs from the QA list and from Sriya's reading, in `app/`. Before every push run `uv run python -m app.meta`, `app.agent`, `app.pipeline` and `app.telegram_bot --selftest`, then `git pull`. Each push redeploys the live site, so push in batches.
  - **Needs:** the QA bug list
  - **Done when:** every reported backend bug is fixed or answered.
- [ ] **Run the Telegram bot (optional)** (30 min)
  - Yasaswini wrote it. In Telegram, talk to @BotFather, send `/newbot` and copy the token. Put it in `.env` as `TELEGRAM_BOT_TOKEN=...`, run `uv run --env-file .env python -m app.telegram_bot`, then in the chat send `/unlock` with the access code and a photo. Steps are in the README.
  - **Needs:** the access code, and Gemini quota for a real check
  - **Done when:** a photo sent to the bot comes back cleaned. Send Yasaswini the error if it does not.

### Sriya: Benchmark, page and write-up

- [ ] **Set up the project on a laptop** (30 min)
  - Install Git and uv. Clone `https://github.com/Yasaswini-ch/snap-safe-india.git`, run `uv sync`, copy `.env.example` to `.env` and put the Google key in it. Get the key from Yasaswini in a private message, and never commit `.env`. Then run `uv run python -m app.meta`; it should print `meta ok`.
  - **Needs:** an invite to the GitHub repo, and the key
  - **Done when:** the self-checks pass and `uv run --env-file .env uvicorn app.main:app` opens the page at localhost:8000.
- [ ] **Check the Telugu and Hindi** (45 min)
  - Read the Indian clues note in `app/regions/india.py`, the Hindi and Telugu "do not report" phrases in `app/meta.py`, the Telugu sign in `bench/india/make_scenes.py` and the page text. Fix wrong or unnatural wording.
  - Also try one Hindi and one Tamil photo through the live site, because only a Telugu sign has been tested. The page already says the checker is “told to read” them, so note what happens.
  - **Needs:** nothing, start now
  - **Done when:** corrections are made or sent to Yasaswini.
- [ ] **Run the benchmark and publish it** (1 h, mostly waiting)
  - Five core scenes by default. Run `uv run --env-file .env python -m bench.indiabench --tag in --verifier gemma-4-26b-a4b-it`, then the same with `REGION=global` set first (PowerShell: `$env:REGION='global'`) and `--tag global`. The verifier option reads the before and after photos with Gemma, which spares Gemini's quota. Then `uv run python -m bench.india.publish`, check the results section at localhost:8000, run `git pull`, commit and push. Then move on to the README numbers.
  - **Needs:** the setup, about 20 Gemini requests per run, and the samples already recorded: everyone using the key shares Gemini's per-minute limit, so never run two Gemini jobs at once
  - **Done when:** the results section shows five scenes on the live page.
- [ ] **Run the other five benchmark scenes (optional)** (1 h, mostly waiting)
  - The rest of the ten: add `--all` to the same commands. Scenes already scored are reused, so only the other five run, and the summary files then cover all ten. The page keeps showing the five core scenes, so this adds depth for the README and the write-up without changing the page.
  - **Needs:** the first benchmark done, and quota or billing
  - **Done when:** both summary files list ten scenes.
- [ ] **Submission write-up (draft ready)** (1.5 h)
  - Title, short description, the problem, what it does, tools used (Gemini 3 Flash, Gemma 4, FastAPI, OpenCV), what we built (India detection, checksum, region packs, benchmark, page) and what it grew out of (before-you-post, MIT). State the limits: the "Verified" tag is the agent's own judgment. A draft is in [write-up.md](write-up.md); edit it and fill in the numbers.
  - **Needs:** benchmark numbers, for the results line
  - **Done when:** text is ready to paste into the event form, with screenshots chosen.
- [ ] **Put the benchmark numbers in the README** (30 min)
  - When the benchmark finishes, replace the Benchmark section of `README.md` with the tables from `bench/india/results/in/summary.md` and `global/summary.md`, and delete the sentence saying the Gemini results are not in yet. Say plainly where a number comes from one run or a small set.
  - **Needs:** the benchmark, run by Sriya
  - **Done when:** the README matches the summary files.
- [ ] **Fix the page bugs from QA** (ongoing)
  - Fix what you find in `static/index.html`: wording, layout, anything that looks wrong on a phone. Open the page locally with `uv run --env-file .env uvicorn app.main:app` to check, run `git pull`, then commit and push. Send backend bugs to Likhitha. Page bugs come from your own reading and from the QA list.
  - **Needs:** the setup
  - **Done when:** every page bug you found is fixed.
- [ ] **Demo script and recording (optional)** (2 h)
  - Three minutes: the problem (a photo with an ID number in it), the before and after slider, the ID-card replay in "The agent at work", the benchmark table, region packs. Record the screen with voice, and a second backup take.
  - **Needs:** samples and results on the page
  - **Done when:** a video file and a backup exist, under 3 minutes.

## Submission text

The draft for the event form is in [write-up.md](write-up.md). The results lines there are placeholders until the benchmark has run. See also [benchmark.md](benchmark.md), [deploy.md](deploy.md) and [demo-script.md](demo-script.md).

## Order of work

- **Now to noon, Oct 31**: Already done: the push to GitHub, the Render deploy, the language option and the bot. Now: both set up the project on a laptop. Likhitha photographs the props. Sriya checks the Telugu and Hindi, then tries a Hindi and a Tamil photo.
- **About 1 PM, Oct 31**: Quota resets about 12:30 PM, or billing is already on. Likhitha records the samples. Sriya starts the benchmark only after the samples are done, since both use the same Gemini limit.
- **Evening, Oct 31**: Likhitha pushes the samples, then Sriya pushes the results (each runs `git pull` first), and Render redeploys by itself. Likhitha runs QA. Sriya puts the numbers in the README and writes the submission. The demo recording is optional.
- **Night, Oct 31**: Freeze: bug fixes only. Submission text is finished and the README is final.
- **Morning, Nov 1, before 10:00**: Everyone rehearses once. Open the Render link to wake it, check the key and quota, keep the backup recording on a phone.
- **Event day**: Submit between 3:45 and 4:15 PM, demo from 4:15 PM.

## What could go wrong

- **Quota.** The free key allows 20 requests a day. Without billing, demo with recorded samples; they play with no key at all.
- **Render sleeps.** The free plan wakes in about a minute. Open the link before presenting.
- **Accuracy.** Gemma and the lite models place boxes less well. The demo uses Gemini 3 Flash or recordings.
- **The "Verified" tag.** It is the agent's own check, not proof. Say so in the demo.
- **Every push redeploys.** The live site rebuilds from `main`. Push in batches, and check the site after each one.
- **Keys.** Never commit a key or paste it in a group chat. Rotate the old one.

_Estimates are rough guesses. Rendered benchmark scenes are not real photos, and every value in them is made up._

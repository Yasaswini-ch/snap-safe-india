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
- All six samples recorded (ID card, parcel label, Telugu sign, number plate, UPI screen, plus a tea stall menu as the nothing-to-hide control) and read back after cleaning. The UPI one leaves the first name visible Three photo-style samples (parcel, payment screen, number plate) are recorded with Gemma 4 too.
- Telegram bot, tested offline and once on real Telegram with the made-up ID card (screenshots in `docs/img`)
- The live page, tested by the team: no problems found
- All ten benchmark scenes run with Gemma 4, pack on and off (47 of 48 against 41 of 48); the other five have no Gemini run yet
- Telugu and Hindi wording read through, with extra Hindi, Telugu and Tamil "do not report" phrases and tests (a Tamil reader should still check the Tamil)
- Submission write-up and the README numbers: filled in with what has run so far (only the demo video link and the access code are left blank)
- Page check on desktop and at phone width: no overflow or layout bugs; one wording fix in the results section
- Pack-off benchmark: all five core scenes run (18 of 19 secrets removed with the pack off, 19 of 19 with it on; see `docs/benchmark.md`). The request counter measured 12 requests for the last two scenes: 8 Gemini, 4 Gemma
- Live Telugu and Hindi reports tried once each on the made-up ID card: right script, no planted value echoed, labels in English (no native-reader review yet)
- A live upload through the agent with the new key (run locally): ID card, safe, nothing left readable
- Offline text-detector benchmark (75 made-up texts plus 14 injection notes): precision 0.937, recall 0.894, F1 0.915 with the India pack on, recall 0.076 with it off; reproducible, no key needed (`bench/detectorbench.py`, results in `bench/india/results/detector`)
- The benchmark now counts the API requests it sends (`bench/requestcount.py`), so the next run reports a measured count, not an estimate
- Offline language tests (`tests/test_language.py`, 11 checks) and request-counter tests (`tests/test_requestcount.py`, 4 checks) pass; the README separates the four kinds of evaluation; the long write-up is `docs/writeup.md`
- Page check at 320 and 375 px: the nav button stuck out of its pill on a phone; fixed

### Blocked

- Gemini 3 Flash is the fast, accurate model. Its free tier gives **20 requests a day per Google project**. The new key has used most of today's. The old key resets around 12:30 PM IST.
- The new key ran out of quota on Oct 31 during the pack-off benchmark, then worked again later the same day and the last two scenes ran. Hindi and Telugu photographs were run afterwards (see `docs/benchmark.md`); Tamil photos are still not tried.
- Fix: switch on billing for the Google AI Studio project, or record only two samples after the reset.

### Not tested yet

- A full live check on the deployed site (it needs the new Google key in Render's settings; the same check passed locally)
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

- [ ] **QA pass** (1 h)
  - On a laptop and a phone: click every sample, type in the caption box, upload one scene from `bench/india/images` as a live check, try dark mode and a narrow window. Write each bug as page, steps, screenshot.
  - **Needs:** the samples recorded
  - **Done when:** the bug list exists: page bugs go to Sriya, backend bugs stay with Likhitha, and fixed bugs are re-checked.
- [ ] **Fix the backend bugs from QA** (ongoing)
  - Fix the backend bugs from the QA list and from Sriya's reading, in `app/`. Before every push run `uv run python -m app.meta`, `app.agent`, `app.pipeline` and `app.telegram_bot --selftest`, then `git pull`. Each push redeploys the live site, so push in batches.
  - **Needs:** the QA bug list
  - **Done when:** every reported backend bug is fixed or answered.

### Sriya: Benchmark, page and write-up

- [ ] **Set up the project on a laptop** (30 min)
  - Install Git and uv. Clone `https://github.com/Yasaswini-ch/snap-safe-india.git`, run `uv sync`, copy `.env.example` to `.env` and put the Google key in it. Get the key from Yasaswini in a private message, and never commit `.env`. Then run `uv run python -m app.meta`; it should print `meta ok`.
  - **Needs:** an invite to the GitHub repo, and the key
  - **Done when:** the self-checks pass and `uv run --env-file .env uvicorn app.main:app` opens the page at localhost:8000.
- [ ] **Try a Hindi and a Tamil photo, and check the Tamil words** (30 min)
  - The wording review is done. What is left: run the two made-up signs through the page and note what happens. Make them with `bench/india/make_scenes.py` style (a shop name, an owner name, a made-up phone number, in Devanagari and Tamil script), or photograph props. Read the Tamil phrases in `app/meta.py` (`TOLD` and `ADDRESSED`) and fix any that are wrong or unnatural. The page already says the checker is "told to read" them, so say what really happens.
  - **Needs:** the setup, and Gemini quota
  - **Done when:** both photos have a result noted in `docs/benchmark.md` limits, and the Tamil words are confirmed or corrected.
- [x] **Finish the pack-off benchmark** (done Oct 31: all five scenes scored; the page results were republished)
  - Three of the five core scenes are done with the pack off: ID card, courier label and number plate (see `docs/benchmark.md`). Left: the **Telugu sign and the control**. Set `REGION=global` first (PowerShell: `$env:REGION='global'`), then `uv run --env-file .env python -m bench.indiabench --tag global --verifier gemma-4-26b-a4b-it`. Scenes already scored are reused. Then `uv run python -m bench.india.publish`, check the results section at localhost:8000, add the two scenes to the pack-off table in `README.md` and `docs/benchmark.md`, change the pack-off line in `docs/write-up.md` from three scenes to five, run `git pull`, commit and push.
  - **Needs:** the setup, about 8 Gemini requests, and no other Gemini job running: everyone using the key shares the per-minute limit
  - **Done when:** the results section shows both columns for all five scenes on the live page.
- [ ] **Fix the page bugs from QA** (ongoing)
  - The desktop and narrow-window pass is done; what is left is a look on a real phone. Fix what you find in `static/index.html`: wording, layout, anything that looks wrong on a phone. Open the page locally with `uv run --env-file .env uvicorn app.main:app` to check, run `git pull`, then commit and push. Send backend bugs to Likhitha. Page bugs come from your own reading and from the QA list.
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

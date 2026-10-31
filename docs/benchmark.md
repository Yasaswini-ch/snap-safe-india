# The Indian benchmark

## What it measures

Ten rendered scenes with **planted fictional secrets**: an ID card, a tax card, a courier label, a number plate, a house
name board, a UPI payment screen, a college lanyard, a wedding invite, a Telugu shop sign, and a control with nothing
personal. The scenes are drawn with Python and styled to look like phone photos. They are not photographs, they are
cleaner than real ones, and every value in them is made up. They are in [bench/india/images](../bench/india/images), with
the planted strings in [bench/india/scenes.json](../bench/india/scenes.json). Five are **core** and run by default: the ID
card, courier label, number plate, Telugu sign and the control. The other five run with `--all`.

## How a scene is scored

1. A verifier model transcribes the original. A planted secret counts only if it was readable there.
2. The agent runs (private mode, so edits are pixelation and inpainting).
3. The verifier transcribes the result. A secret that is still readable in it counts as a miss.

Scoring is strict about names: a multi-word name or place also counts **word by word** (four letters or more), so a
half-hidden name is a leak. Other numbers reported: the share of the frame changed, whether the attacker flagged each leak
scene and wrongly flagged the control, whether the regex text check found the expected ID types, whether the attacker's
report echoed a planted value, and seconds per scene.

## Run it

```bash
uv run --env-file .env python -m bench.indiabench --tag in --verifier gemma-4-26b-a4b-it
REGION=global uv run --env-file .env python -m bench.indiabench --tag global --verifier gemma-4-26b-a4b-it
uv run python -m bench.india.publish      # fills the page's results section
```

On Windows PowerShell set the region first: `$env:REGION='global'`. `--all` runs all ten scenes, and scenes already scored
in the results folder are reused, so a later `--all` run adds the rest. `--verifier` reads the before and after photos with
another model, which spares the attacker's quota and makes the check independent. `REGION=global` switches the India
pack off, so the difference between the two runs is what the pack adds.

## Results

### First run, Gemma 4, lenient scoring (full names only)

Archived in `bench/india/results/in-gemma4` and `global-gemma4`. One run each, ten scenes.

| | India pack on | India pack off |
|---|---|---|
| Planted secrets removed | 26 of 26 | 24 of 26 |
| Scenes with every secret removed | 9 of 9 | 8 of 9 |
| Share of the photo changed | 7.0% | 8.2% |

With the pack off the model missed the whole PAN card and changed twice as much of the courier label. The scoring was too
lenient: it counted a half-hidden name as removed, which a recorded Gemma sample later showed is wrong. Treat these as
a first look.

### Gemini 3 Flash, India pack on, four of the five core scenes

Oct 31, 2026. Model that found the clues: `gemini-3-flash-preview`. Model that read the photos: `gemma-4-26b-a4b-it`. One run, with
strict scoring and box snapping on. **This run came before the final literal check was added to the agent.** The control scene
did not run, because the key's daily quota ran out, and the pack-off run was not done for the same reason.

| | India pack on |
|---|---|
| Planted secrets removed | 11 of 19 (58%) |
| Scenes with every secret removed | 2 of 4 |
| Share of the photo changed (mean) | 7.1% |
| Leak scenes flagged | 4 of 4 |
| Text check found the expected ID types | 4 of 4 |
| Values echoed in the report | 1 of 14 |
| Mean seconds per scene | 44 |

| Scene | Secrets removed | Changed |
|---|---|---|
| ID card | 2 of 7 (name and PIN still readable) | 4.1% |
| Courier label | 7 of 7 | 17.3% |
| Number plate | 1 of 1 | 2.8% |
| Telugu sign | 1 of 4 | 4.3% |

This is much weaker than the recordings in the sample gallery, which were single runs we picked and checked by hand. The ID card
came out clean in a recorded run and left the name and PIN readable here, with the edit sitting just below the name line. The
agent still called that result safe, because its own re-check missed it. That is the failure the final literal check targets
(see [how-it-works.md](how-it-works.md)); the scenes need to be run again with it. Raw per-scene files go in
`bench/india/results/in` and are committed with the rerun.

### Rerun with the final check and the icon rule, five core scenes

Same day, same model (`gemini-3-flash-preview`), the photos read by `gemma-4-26b-a4b-it`, India pack on, one run per scene. After
the run above, the agent gained a final literal read of the edited photo and a prompt rule against boxing status icons.
The ID card, the Telugu sign and the control were rerun with them. **The courier label and the number plate were not rerun**:
their results are from the run above, before those changes. So this table mixes two code versions, and it is one run each.

| | India pack on |
|---|---|
| Planted secrets removed | 19 of 19 |
| Scenes with every secret removed | 4 of 4 |
| Share of the photo changed (mean) | 8.8% |
| Leak scenes flagged | 4 of 4 |
| Control falsely flagged | 0 of 1 |
| Text check found the expected ID types | 3 of 4 |
| Values echoed in the report | 0 of 14 |
| Mean seconds per scene | 59 |

| Scene | Secrets removed | Changed | Code version |
|---|---|---|---|
| ID card | 7 of 7 (2 of 7 before) | 6.4% | with the final check |
| Courier label | 7 of 7 | 17.3% | before it |
| Number plate | 1 of 1 | 2.8% | before it |
| Telugu sign | 4 of 4 (1 of 4 before) | 17.6% | with the final check |
| Control | nothing to remove, nothing edited | 0.0% | with the final check |

The two scenes that failed before now pass, which is what the final check is for, but two scenes are a small sample and the
rerun is the same scenes the fix was aimed at, so this shows the fix works on them and not that the agent is reliable in
general. The text check missed the PIN code on the ID card in this run's transcription (it found the Aadhaar number and the
street address), which is why that row reads 3 of 4. The recorded sample gallery is separate from this benchmark.

### India pack off

Oct 31, 2026, `REGION=global`, `gemini-3-flash-preview`, photos read by `gemma-4-26b-a4b-it`, one run per scene. The ID card, courier
label and number plate ran first; the quota then ran out, and the Telugu sign and the control were run afterwards the same day. All
five core scenes are now scored. Raw files are in `bench/india/results/global`.

| Scene | Pack off | Pack on (final-check version) | Changed, pack off |
|---|---|---|---|
| ID card | 7 of 7 | 7 of 7 | 7.6% |
| Courier label | 6 of 7 | 7 of 7 (before the final check) | 16.0% |
| Number plate | 1 of 1 | 1 of 1 (before the final check) | 2.9% |
| Telugu sign | 4 of 4 | 4 of 4 | 13.6% |
| Control | nothing to remove, nothing edited | same | 0.0% |

| Pack off, all five scenes | Result |
|---|---|
| Planted secrets removed | 18 of 19 (95%) |
| Scenes with every secret removed | 3 of 4 |
| Share of the photo changed (mean) | 8.0% |
| Leak scenes flagged | 4 of 4 |
| Control falsely flagged | 0 of 1 |
| Values echoed in the report | 1 of 14 |
| Mean seconds per scene | 109 (one run, rough) |

With the pack off, 18 of 19 planted secrets were removed, against 19 of 19 with it on. That is one secret (on the courier label) in one
run, so it is not evidence that the pack matters for these scenes. The pack-on courier-label and number-plate results come from
before the final check was added, so the two columns are not a clean comparison. The text check found none of the expected ID
types, as expected with the pack off; its effect is measured in the offline detector benchmark below.

### Gemma 4 on the same scenes

Oct 31, 2026. All ten scenes, `gemma-4-26b-a4b-it` as both attacker and reader, current code (strict scoring, box snapping, final check),
one run each, with the India pack on and off. Raw files: `bench/india/results/in-gemma-all` and `global-gemma-all`. The car plate scene hit Gemma
server errors (HTTP 500) in the first pass of each run and was rerun on its own, so the per-run request counts in the summary files cover only the
last invocation.

| | India pack on | India pack off |
|---|---|---|
| Planted secrets removed | 47 of 48 (98%) | 41 of 48 (85%) |
| Scenes with every secret removed | 8 of 9 | 6 of 9 |
| Share of the photo changed (mean) | 6.7% | 6.3% |
| Leak scenes flagged | 9 of 9 | 9 of 9 |
| Control falsely flagged | 0 of 1 | 0 of 1 |
| Text check found the expected ID types | 8 of 8 | 0 of 8 |
| Values echoed in the report | 2 of 34 | 0 of 34 |
| Mean seconds per scene | 200 | 203 |

Per scene, secrets removed with the pack on / off: ID card 7/7 and 6/7, tax card 5/5 and 5/5, courier label 7/7 and 7/7, number plate 1/1 and 1/1,
house name board 5/6 and 2/6, UPI screen 4/4 and 4/4, Telugu sign 4/4 and 4/4, college lanyard 6/6 and 4/6, wedding invite 8/8 and 8/8, control 0/0 and 0/0.

The pack is worth about seven secrets of 48 here, mostly on the house name board, the college lanyard and the ID card, and it is what lets the regex
text check find the ID types at all. That is one run per setting with the weaker model, and the gap sits in three scenes, so it could shift on another
run. Two planted values were echoed in the attacker's report with the pack on (the pack off echoed none), which is a miss for the "never prints values"
claim and is not explained by this run alone.

### The other five scenes

Included in the ten-scene Gemma 4 run above. The Gemini 3 Flash runs cover only the five core scenes; the other five (tax card, house name board, UPI screen, college lanyard, wedding invite) have no Gemini results yet.

## Photograph-like images (one run each; first four incomplete)

Seven images supplied by the team (`bench/india/photos`, with `scenes.json`). They look like photographs, not drawn scenes, and every value in them is
meant to be fictional. They were re-saved as JPEG, which leaves no EXIF or GPS data. Run with
`uv run --env-file .env python -m bench.indiabench --set photos --tag photos-in --verifier gemma-4-26b-a4b-it`
(`--set` needs its own `--tag`, so the published results are never overwritten). Results: `bench/india/results/photos-in`.
Scenes already scored are reused, so the file mixes two runs, as described below.

| Scene | What is in it | Secrets removed (Gemma read) | Changed | Attacks | Marked safe |
|---|---|---|---|---|---|
| Tea menu | control: chalkboard menu | nothing to remove, nothing edited | 0.0% | 1 | yes |
| Medical shop sign | Telugu and English sign, phone number, scooter plate | 3 of 4 (the Telugu shop name was still readable) | 5.9% | 1 | no |
| Library card | name, address, PIN, member number on a card | 10 of 10 | 11.9% | 1 | no |
| House gate | name plate and a PIN plate | 7 of 7 | 12.0% | 1 | no |
| UPI shop (Hindi) | PhonePe stand with QR and UPI ID, Hindi shop name and price list | 2 of 2 | 13.9% | 3 | yes |
| Hindi parcel | Hindi name and address, PIN, mobile, order and AWB numbers | 8 of 8 | 24.1% | 3 | yes |
| Telugu house plate | Telugu house name, number, colony, town, PIN, phone | 6 of 6 | 8.3% | 4 | no |

- **Incomplete first four.** In the first run (four scenes) Gemini 3 Flash's free daily quota (20 requests) ran out: 9 of 27 requests got a 429. Those scenes
  finished, but the re-attack did not, so "safe" is no and the exposure after is just the exposure before. Their scores are one Gemma read only.
- **Complete last three.** With a new key (22 requests: 15 Gemini, 7 Gemma, one Gemma request failed with a 500 and was retried), the UPI shop, the Hindi
  parcel and the Telugu house ran to the end. The Hindi parcel and the UPI shop were marked safe by the agent; the Telugu house reached the
  four-attack limit with exposure still "specific" for the home (level 3), so it was not marked safe.
- **First live Hindi photo.** The Hindi parcel (Devanagari name, address and mobile) and the Hindi shop sign were read and edited. The text check found the
  PIN code and phone number on the parcel and the UPI ID on the shop stand.
- **What the scores miss.** Looking at the edited images ourselves: the pixelation boxes are often offset from the text they are meant to cover. On the
  Telugu house plate the first line (`శ్రీ లక్ష్మ…`), the start of the house-number line (`ఇంటి నం. 12`) and the start of the colony name are still readable,
  yet the Gemma read scored all six secrets as removed, because a secret counts as removed only when the whole string is gone. On the Hindi parcel the
  label is mostly covered but one box sits above it, and a strip of the "DEL" box remains. So for Telugu and Hindi photos these scores are optimistic. Scoring
  also compares text with combining marks (vowel signs) dropped, which makes Indic matching looser still.
- **Heavy and offset edits.** The card, the name plates and the parcel label were pixelated more than the secrets need, and the shop sign's block was larger
  than the phone number.

- **On the page.** All seven are in the sample gallery as recordings made with Gemma 4 (`app/samples.py`, names `in_photo_*`), so they also play in "The agent at
  work", and in the "Photo-style images" results section (`bench/india/photos/publish.py`). The recordings are separate runs: the agent marked all
  seven safe in them, which is its own judgment and differs from the Gemini benchmark run for the Telugu house plate. The Hindi parcel and the Telugu house
  plate recordings, which we looked at, hide the address lines and the phone number well; the Telugu house name stays visible.

Treat all of this as a first look: one run per scene, a noisy verifier, and no re-check on four of the seven. Rerun the first four with `--force` after the
quota resets, and have someone read the Telugu and Hindi after-images. Confirm that the photos contain no real person's details before the repo stays public.

## Text detector benchmark (offline, no model)

This is separate from the image benchmark above and below. It scores only the deterministic text check that runs beside the
model (`meta.text_check`: the regular expressions, the Aadhaar Verhoeff checksum and the note-to-AI detector), so it needs no key
and gives the same scores every run.

- **Dataset:** [bench/india/detector_cases.json](../bench/india/detector_cases.json): 75 hand-written detail texts (57 contain at least one
  private detail, 18 contain nothing private: 16 look-alikes such as tracking numbers, order numbers and dates, plus a tea menu and
  an empty photo) and 14 injection-note texts. All values are made up. The labels were written from the text alone, before the
  detector was run, and were not changed afterwards to improve the score. The groups are `positive` (ordinary formats),
  `hard_negative` (look-alikes), `known_limit` (real formats the patterns are not built for) and `scene_like` (mimic the benchmark scenes).
- **Scoring:** per text and per kind of detail. TP: the kind is in the text and was found. FP: found but not in the text. FN: in
  the text but missed. Several matches of one kind in one text count once. Precision is TP/(TP+FP), recall TP/(TP+FN), F1 their
  harmonic mean; macro F1 averages the kinds.
- **Commands:** `uv run python -m bench.detectorbench --tag in`, and for the pack-off row `$env:REGION='global'; uv run python -m bench.detectorbench --tag global` (PowerShell).
  Output: `bench/india/results/detector/in.{md,json}` and `global.{md,json}`. The run is deterministic: two runs gave identical scores.

| | TP | FP | FN | Precision | Recall | F1 | Macro F1 |
|---|---|---|---|---|---|---|---|
| India pack on | 59 | 4 | 7 | 0.937 | 0.894 | 0.915 | 0.898 |
| India pack off | 5 | 0 | 61 | 1.000 | 0.076 | 0.141 | 0.121 |

Injection-note detector, pack on or off (it does not depend on the pack): TP 6, FP 1, FN 1, TN 6; precision 0.857, recall 0.857, F1 0.857.
With the pack off, precision is 1.000 only because it found 5 things in total.

**Pack on, by kind**

| Kind | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| Aadhaar number | 8 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| GSTIN | 1 | 0 | 1 | 1.000 | 0.500 | 0.667 |
| IFSC code | 2 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| PAN number | 4 | 0 | 1 | 1.000 | 0.800 | 0.889 |
| PIN code | 6 | 1 | 0 | 0.857 | 1.000 | 0.923 |
| UPI ID | 7 | 0 | 1 | 1.000 | 0.875 | 0.933 |
| email address | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| phone number | 10 | 0 | 1 | 1.000 | 0.909 | 0.952 |
| street address | 10 | 1 | 1 | 0.909 | 0.909 | 0.909 |
| vehicle plate | 6 | 1 | 2 | 0.857 | 0.750 | 0.800 |
| voter ID number | 2 | 1 | 0 | 0.667 | 1.000 | 0.800 |

**Pack on, by kind of test text**

| Group | TP | FP | FN | Precision | Recall |
|---|---|---|---|---|---|
| positive | 42 | 0 | 0 | 1.000 | 1.000 |
| hard_negative | 0 | 4 | 0 | 0.000 | n/a |
| known_limit | 0 | 0 | 7 | n/a | 0.000 |
| scene_like | 17 | 0 | 0 | 1.000 | 1.000 |

**Pack off, by kind** (the India kinds are all missed; only the generic patterns remain)

| Kind | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| Aadhaar number | 0 | 0 | 8 | n/a | 0.000 | 0.000 |
| GSTIN | 0 | 0 | 2 | n/a | 0.000 | 0.000 |
| IFSC code | 0 | 0 | 2 | n/a | 0.000 | 0.000 |
| PAN number | 0 | 0 | 5 | n/a | 0.000 | 0.000 |
| PIN code | 0 | 0 | 6 | n/a | 0.000 | 0.000 |
| UPI ID | 0 | 0 | 8 | n/a | 0.000 | 0.000 |
| email address | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| phone number | 1 | 0 | 10 | 1.000 | 0.091 | 0.167 |
| street address | 1 | 0 | 10 | 1.000 | 0.091 | 0.167 |
| vehicle plate | 0 | 0 | 8 | n/a | 0.000 | 0.000 |
| voter ID number | 0 | 0 | 2 | n/a | 0.000 | 0.000 |

**Missed, pack on (all 7 are known limits):** lowercase PAN (`pan_lowercase`), a GSTIN ending in a letter (`gstin_letter_end`),
a Delhi plate with a letter inside the number (`plate_delhi_letter_in_number`), a lowercase plate (`plate_lowercase`), a UPI handle
that is not in the list (`upi_handle_not_listed`), Devanagari-digit phone numbers (`phone_devanagari_digits`) and an address
in Telugu script (`address_telugu_script`).
**False alarms, pack on:** `INV2024001` as a voter ID, `KB 07 C 2025` as a plate, `Ref-123456` as a PIN code, "Open Colony Sale" as an address.
**Injection mistakes:** a paraphrased instruction was missed (`inj_paraphrase`); "Assistant Professor notice: do not report late for class" was flagged.

**Timing.** Measured on one Windows laptop with Python 3.11: the whole run (loading, scoring and 200 timing passes) took 0.2 to 0.5 s
across runs; one pass over all 89 texts took about 1 to 3 ms, roughly 0.01 to 0.03 ms per text. These depend on the machine and
change each run. The committed files hold one run.

**What this does not show.**
- The texts are synthetic and written by us. They show how the patterns behave on formats we thought of, not how often they
  fire on real photos or real OCR output.
- The share of known-limit and look-alike cases was chosen by us and moves the totals. Read the by-group table, not only the F1.
- It scores no model and no photo edit. **There is no image-level precision, recall or F1 anywhere in this repo**: a photo has no agreed
  list of every clue, so false positives and false negatives would be guesses.
- The Tamil note phrases added on Oct 31 are not in this dataset, and the detector has no Tamil or Telugu number or address patterns.
- The detector was not tuned after seeing these results. Fixing the known misses (case-insensitive PAN and plates, GSTIN
  last character, more UPI handles, Devanagari digits) is future work.

## API request counter

`bench/indiabench.py` counts every HTTP request it sends to the model API, through the OpenAI client's own HTTP hooks
(`bench/requestcount.py`), so the number includes the client's automatic retries after a 429 or a server error, every extra
attack round, and requests that never got an answer. Each request is labelled by model, by role (`verifier`: the before and
after reads of a scene; `agent`: the attacker and the agent's own text checks), by type (`attack` for a scene's first attack,
`attack_more` for every later one, `transcribe`, `link`, `caption`) and by HTTP status. Nothing from the request itself is
stored. After a run the totals are printed, appended to `summary.md`, and saved as `requests-<time>.json`; each scene's JSON
also carries its own counts. Scenes reused from earlier runs send nothing, so their requests are not counted and the summary
says so. **One real run has been counted** (Oct 31, pack off, the Telugu sign and the control, Gemini 3 Flash attacker, Gemma 4 verifier):
**12 requests, all answered with 200, none retried or failed.** By model: 8 to `gemini-3-flash-preview` and 4 to `gemma-4-26b-a4b-it`.
By role: 8 agent and 4 verifier. By type: 2 first attacks, 2 later attacks, 8 transcriptions. That is 4 Gemini requests per scene
here, but the control needed 1 attack and the Telugu sign 3, and two scenes are too few to give a per-run figure for five scenes,
so the earlier estimate of about 20 requests per five-scene run is still an estimate. The numbers are in
`bench/india/results/global/requests-20261031-153020.json`. The counter is tested offline against a stand-in API
(`uv run python -m tests.test_requestcount`).
### Realistic photos, Gemma 4, three scenes

Oct 31, 2026. Three photo-style images made with an image model from prompts with made-up values (a courier parcel on a doorstep, a payment
screen at a shop counter, a red hatchback at a gate), in [bench/india/real](../bench/india/real). Attacker and reader both `gemma-4-26b-a4b-it`,
because the Gemini key was out of quota that day. India pack on, one run each, private mode.

| Photo | Secrets removed | Frame changed | Seconds |
|---|---|---|---|
| Parcel | 9 of 9 | 11.4% | 235 |
| Payment screen | 5 of 5 | 1.1% | 184 |
| Number plate | 1 of 1 | 1.5% | 96 |

Secrets are counted word by word for names, as in the rest of this page (15 of 15 in all). All three ended with nothing readable in the edited photo, and the attacker's report echoed none of the values. The plate and the payment
screen are clean edits (the amount and the green tick stay). The parcel is not: the label is hidden, but the boxes are much larger than the label
and spill onto the wall, the door and the doormat, because the box is tilted in the photo. It leaks nothing and looks wrong. This is the box
over-sizing already named in the limits, worse on a photograph than on a rendered scene. One run each with the weaker model, so it shows the agent
works on photographs and not how often. Run again with Gemini 3 Flash after the quota resets.
Reproduce with `bench/india/real/run.py`; `bench/india/real/publish.py` puts them on the page.

## Limits

- Rendered scenes, one run per setting, and a small set, so a gap of one or two secrets can be luck.
- The verifier is the same kind of model as the attacker unless `--verifier` names another.
- It scores text only. Faces, landmarks and other non-text clues are attacked but not scored.
- Hindi photos were run only in the photograph-like set (a parcel and a UPI shop stand, one run each); Tamil photos have not been tested. The attacker samples, so numbers move between runs.

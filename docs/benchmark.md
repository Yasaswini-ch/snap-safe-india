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

Oct 31, 2026, `REGION=global`, `gemini-3-flash-preview`, photos read by `gemma-4-26b-a4b-it`, one run per scene. **Partial: three of
the five core scenes.** The key's daily quota (20 requests per model) ran out, so the Telugu sign and the control errored and are not
scored. Raw files are in `bench/india/results/global`.

| Scene | Pack off | Pack on (final-check version) | Changed, pack off |
|---|---|---|---|
| ID card | 7 of 7 | 7 of 7 | 7.6% |
| Courier label | 6 of 7 | 7 of 7 (before the final check) | 16.0% |
| Number plate | 1 of 1 | 1 of 1 (before the final check) | 2.9% |

With the pack off, 14 of 15 planted secrets were removed, against 15 of 15 on these same three scenes with it on. That is one secret
on one scene in one run, so it is not evidence that the pack matters. The text check found none of the expected ID types, as expected with
the pack off. The Telugu sign and the control still need a run once the quota resets.

### Gemma 4 on the same scenes

_To add: the same table for Gemma, with box snapping and the detail wording on._

### The other five scenes

_To add if run with `--all`._

## Limits

- Rendered scenes, one run per setting, and a small set, so a gap of one or two secrets can be luck.
- The verifier is the same kind of model as the attacker unless `--verifier` names another.
- It scores text only. Faces, landmarks and other non-text clues are attacked but not scored.
- The benchmark does not test Hindi or Tamil photos, and the attacker samples, so numbers move between runs.

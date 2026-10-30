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

### Five core scenes, strict scoring

_To add after the run. Model that found the clues: ______. Model that read the photos: ______. Date: ______._

| | India pack on | India pack off |
|---|---|---|
| Planted secrets removed | _ of _ | _ of _ |
| Scenes with every secret removed | _ of _ | _ of _ |
| Share of the photo changed (mean) | _% | _% |
| Leak scenes flagged | _ of _ | _ of _ |
| Control falsely flagged | _ of _ | _ of _ |
| Text check found the expected ID types | _ of _ | _ of _ |
| Values echoed in the report | _ of _ | _ of _ |
| Mean seconds per scene | _ | _ |

Per-scene tables are in `bench/india/results/<tag>/summary.md`.

### Gemma 4 on the same scenes

_To add: the same table for Gemma, with box snapping and the detail wording on._

### The other five scenes

_To add if run with `--all`._

## Limits

- Rendered scenes, one run per setting, and a small set, so a gap of one or two secrets can be luck.
- The verifier is the same kind of model as the attacker unless `--verifier` names another.
- It scores text only. Faces, landmarks and other non-text clues are attacked but not scored.
- The benchmark does not test Hindi or Tamil photos, and the attacker samples, so numbers move between runs.

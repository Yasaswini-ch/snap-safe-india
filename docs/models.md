# Models, quotas and what we tried

Any OpenAI-compatible vision model works through `OPEN_API_BASE` and `OPEN_MODEL` (see [deploy.md](deploy.md)). This page
records what we measured. Every number here is from a handful of runs on a few rendered scenes, not a benchmark.

## Models

| Model | What we saw | Use |
|---|---|---|
| `gemini-3-flash-preview` | First test on the ID card: every value hidden in 53 s, nothing readable afterwards, boxes on the text. Recorded samples took 43 to 111 s. In one recording the boxes were coarser and also covered part of the card title. | Demo model |
| `gemma-4-26b-a4b-it` | Free quota that was still available when Gemini's ran out. 50 to 135 s per attack. Boxes often in the wrong places: a recorded run left "Teja Kondapalli" readable, and a live wedding-invite run left the RSVP phone number visible after two rounds. | Free fallback |
| `gemini-3.1-flash-lite`, `gemini-3.5-flash-lite` | 3 to 4 s. As a first attack they return one box around the whole card. | Not used |
| `gemma-4-31b-it` | Returned a server error every time we tried it. | Not used |
| `gemini-2.5-flash` and `-lite` | Not available to new keys. | n/a |

Gemma 4 here is the 26B model only.

## Quotas

- The Gemini free tier gave **20 requests a day per model per Google project** for Gemini 3 Flash, and 5 a minute. A key
  from another project has its own 20. Gemma's quota is separate and was not the limit.
- One full check uses about 3 to 5 requests of the attacking model. A benchmark run on five scenes uses roughly 20.
- `OPEN_RPM` spaces our calls under the per-minute limit. Without it, parallel jobs got 429 errors.
- Billing removes the daily limit. Two jobs on the same key share the per-minute limit, so run one at a time.

## What did not work

- **The lite model as the re-checker.** In a one-photo test it flagged an unedited PAN card and passed a clean ID card. In
  a full run it boxed the whole card every round, so the agent pixelated nearly the whole photo and still reported
  "exact". A short test was not enough; test inside the full loop.
- **Asking Gemma for boxes with the vertical coordinate first** (Gemini's native order). On the ID card both orders edited
  9.5% of the photo and left nothing readable. On the wedding invite it edited 15% instead of 21%, but both orders left
  the date readable. Two scenes, one run each: a weak negative.
- **Gemma's output**: it writes its reasoning inline as `<thought>` blocks and rejects any thinking setting. A forced tool
  call timed out, so Gemma runs in JSON mode with the schema in the prompt.

## Box accuracy

The boxes decide how much of the photo is edited and whether a secret survives, so this is the weakest part.

| Setting | Effect | Measured |
|---|---|---|
| `BOX_SNAP=1` (default) | Shrinks each box to the ink inside it | Recorded Gemini boxes, first round of edits, read back with Gemma. ID card: edited 22.8% to 16.4%. Courier label: 43.2% to 43.1%, because the whole label is text. Telugu sign: 20.2% to 18.6%. Snapping left nothing new readable in any of the three: the ID card and label came out clean both ways, and the shop name on the sign stayed readable both ways (the full run hides it in a later round). Three scenes, one run each |
| `BOX_FOCUS=detail` (off by default) | Asks for a box around the line or number, not the object | Gemma, first round of edits only, one run per scene. Courier label: 20.8% edited and nothing readable with the object wording, 9.7% edited but the surname "Reddy" readable with the detail wording. ID card: 6.8% against 8.5%, and the name and date of birth stayed readable either way. Telugu sign: 17.3% against 18.7%, nothing readable. Mixed, so it stays off |

## Results to add

- _Gemini 3 Flash, five core scenes, India pack on and off: see [benchmark.md](benchmark.md)._
- _Gemma 4, five core scenes, with snapping and the detail wording: see [benchmark.md](benchmark.md)._

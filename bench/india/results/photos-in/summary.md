# Indian benchmark results (2026-10-31, REGION=in, photo set, model gemini-3-flash-preview, photos read by gemma-4-26b-a4b-it)

4 scenes scored (3 leak, 1 control), 0 errors. 21 planted secrets were legible in the originals and are the ground truth below.

Photograph-like images supplied by the team (set 'photos'); every value in them is meant to be fictional. One run each: the attacker samples.

**Incomplete run.** Gemini 3 Flash's free daily quota (20 requests) ran out during this run: 9 of the 27 requests got a 429. All four scenes
finished, but in each leak scene the agent's re-attack did not complete, so "safe" is False and the exposure after equals the exposure
before (it was not re-measured). The "secrets removed" numbers come from a separate read of the edited photo by Gemma 4, one read each,
so they are real but noisy. Rerun after the quota resets (`--force`) for a complete run.

| Metric | Result |
|---|---|
| Planted secrets removed | 20/21 (95%) |
| Scenes with every secret removed | 2/3 (67%) |
| Share of the frame changed (mean) | 7.5% |
| Leak scenes flagged (worst exposure specific or exact) | 3/3 (100%) |
| Control scenes falsely flagged | 0/1 (0%) |
| Text check found the expected kinds | 3/3 (100%) |
| Values echoed in the attacker's report | 1/17 (6%) |
| Mean seconds per scene | 100 |

| Scene | Secrets removed | Changed | Text check found | Edits |
|---|---|---|---|---|
| photo_tea_menu | 0/0 | 0.0% | - | 0 |
| photo_medical_sign | 3/4 | 5.9% | phone number, vehicle plate | 2 |
| photo_library_card | 10/10 | 11.9% | Aadhaar number, PIN code, street address | 3 |
| photo_house_board | 7/7 | 12.0% | PIN code | 2 |

## API requests sent by this invocation (counted)

Every request that actually went out, retries included. Provider quota is per model, so read the by-model rows.

| Requests actually sent | Count |
|---|---|
| Total (including retries) | 27 |
| Answered with an error or not at all | 9 |
| **By role** | |
| agent | 19 |
| verifier | 8 |
| **By model** | |
| gemini-3-flash-preview | 19 |
| gemma-4-26b-a4b-it | 8 |
| **By model and role** | |
| gemini-3-flash-preview / agent | 19 |
| gemma-4-26b-a4b-it / verifier | 8 |
| **By request type** | |
| attack | 4 |
| attack_more | 10 |
| transcribe | 13 |
| **By outcome (HTTP status)** | |
| 200 | 18 |
| 429 | 9 |

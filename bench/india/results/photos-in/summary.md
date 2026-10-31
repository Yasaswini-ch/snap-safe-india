# Indian benchmark results (2026-10-31, REGION=in, photo set, model gemini-3-flash-preview, photos read by gemma-4-26b-a4b-it)

7 scenes scored (6 leak, 1 control), 0 errors. 37 planted secrets were legible in the originals and are the ground truth below.

Photograph-like images supplied by the team (set 'photos'); every value in them is meant to be fictional. One run each: the attacker samples.

**Two runs are mixed in this file.** The first four scenes (tea menu, medical sign, library card, house board) come from an earlier run in which
Gemini's free daily quota ran out: their re-attack did not complete, so they are not verified and the exposure after equals the exposure before.
The last three (UPI shop, Hindi parcel, Telugu house) ran to completion with a new key (3 or 4 attacks each). The totals below add both,
so read the per-scene rows. "Secrets removed" comes from a Gemma 4 read of the edited photo, one read each, scoring whole strings, so a
partly readable line can still count as removed (see docs/benchmark.md).

| Metric | Result |
|---|---|
| Planted secrets removed | 36/37 (97%) |
| Scenes with every secret removed | 5/6 (83%) |
| Share of the frame changed (mean) | 10.9% |
| Leak scenes flagged (worst exposure specific or exact) | 6/6 (100%) |
| Control scenes falsely flagged | 0/1 (0%) |
| Text check found the expected kinds | 6/6 (100%) |
| Values echoed in the attacker's report | 1/33 (3%) |
| Mean seconds per scene | 134 |

| Scene | Secrets removed | Changed | Text check found | Edits |
|---|---|---|---|---|
| photo_tea_menu | 0/0 | 0.0% | - | 0 |
| photo_medical_sign | 3/4 | 5.9% | phone number, vehicle plate | 2 |
| photo_library_card | 10/10 | 11.9% | Aadhaar number, PIN code, street address | 3 |
| photo_house_board | 7/7 | 12.0% | PIN code | 2 |
| photo_upi_kirana | 2/2 | 13.9% | UPI ID | 4 |
| photo_hindi_parcel | 8/8 | 24.1% | PIN code, phone number | 6 |
| photo_telugu_house | 6/6 | 8.3% | PIN code, phone number | 4 |

## API requests sent by this invocation (counted)

Every request that actually went out, retries included. Provider quota is per model, so read the by-model rows.

| Requests actually sent | Count |
|---|---|
| Total (including retries) | 22 |
| Answered with an error or not at all | 1 |
| **By role** | |
| agent | 15 |
| verifier | 7 |
| **By model** | |
| gemini-3-flash-preview | 15 |
| gemma-4-26b-a4b-it | 7 |
| **By model and role** | |
| gemini-3-flash-preview / agent | 15 |
| gemma-4-26b-a4b-it / verifier | 7 |
| **By request type** | |
| attack | 3 |
| attack_more | 7 |
| transcribe | 12 |
| **By outcome (HTTP status)** | |
| 200 | 21 |
| 500 | 1 |

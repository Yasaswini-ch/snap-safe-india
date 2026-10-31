# Indian benchmark results (2026-10-31, REGION=in, photo set, model gemini-3-flash-preview, photos read by gemma-4-26b-a4b-it)

8 scenes scored (7 leak, 1 control), 1 errors. 43 planted secrets were legible in the originals and are the ground truth below.

Photograph-like images supplied by the team (set 'photos'); every value in them is meant to be fictional. One run each: the attacker samples.

**Three runs are mixed in this file.** The first four scenes (tea menu, medical sign, library card, house board) come from an earlier run in which
Gemini's free daily quota ran out: their re-attack did not complete, so they are not verified. The next three (UPI shop, Hindi parcel, Telugu house)
ran to completion with a new key. The last two (Tamil shop sign, Tamil clinic sign) were attempted after the quota ran out again: the shop sign
got no result (counted above as an error) and the clinic sign an unfinished one. The Tamil signs were then run with Gemma 4 instead: see
`../photos-gemma/summary.md` and docs/benchmark.md. The totals below add everything here, so read the per-scene rows. "Secrets removed" comes
from a Gemma 4 read of the edited photo, one read each, scoring whole strings, so a partly readable line can still count as removed.

| Metric | Result |
|---|---|
| Planted secrets removed | 42/43 (98%) |
| Scenes with every secret removed | 6/7 (86%) |
| Share of the frame changed (mean) | 15.0% |
| Leak scenes flagged (worst exposure specific or exact) | 7/7 (100%) |
| Control scenes falsely flagged | 0/1 (0%) |
| Text check found the expected kinds | 7/7 (100%) |
| Values echoed in the attacker's report | 1/37 (3%) |
| Mean seconds per scene | 129 |

| Scene | Secrets removed | Changed | Text check found | Edits |
|---|---|---|---|---|
| photo_tea_menu | 0/0 | 0.0% | - | 0 |
| photo_medical_sign | 3/4 | 5.9% | phone number, vehicle plate | 2 |
| photo_library_card | 10/10 | 11.9% | Aadhaar number, PIN code, street address | 3 |
| photo_house_board | 7/7 | 12.0% | PIN code | 2 |
| photo_upi_kirana | 2/2 | 13.9% | UPI ID | 4 |
| photo_hindi_parcel | 8/8 | 24.1% | PIN code, phone number | 6 |
| photo_telugu_house | 6/6 | 8.3% | PIN code, phone number | 4 |
| photo_tamil_store | error: MemoryError:  | | | |
| photo_tamil_clinic | 6/6 | 43.5% | PIN code, phone number | 9 |

## API requests sent by this invocation (counted)

Every request that actually went out, retries included. Provider quota is per model, so read the by-model rows.

| Requests actually sent | Count |
|---|---|
| Total (including retries) | 13 |
| Answered with an error or not at all | 4 |
| **By role** | |
| agent | 9 |
| verifier | 4 |
| **By model** | |
| gemini-3-flash-preview | 9 |
| gemma-4-26b-a4b-it | 4 |
| **By model and role** | |
| gemini-3-flash-preview / agent | 9 |
| gemma-4-26b-a4b-it / verifier | 4 |
| **By request type** | |
| attack | 2 |
| attack_more | 5 |
| transcribe | 6 |
| **By outcome (HTTP status)** | |
| 200 | 9 |
| 429 | 3 |
| 500 | 1 |

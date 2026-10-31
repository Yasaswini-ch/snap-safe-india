# Indian benchmark results (2026-10-31, REGION=global, model gemini-3-flash-preview)

5 scenes scored (4 leak, 1 control), 0 errors. 19 planted secrets were legible in the originals and are the ground truth below.

The scenes are rendered, not photographed, and every value is fictional. One run each: the attacker samples.

| Metric | Result |
|---|---|
| Planted secrets removed | 18/19 (95%) |
| Scenes with every secret removed | 3/4 (75%) |
| Share of the frame changed (mean) | 8.0% |
| Leak scenes flagged (worst exposure specific or exact) | 4/4 (100%) |
| Control scenes falsely flagged | 0/1 (0%) |
| Text check found the expected kinds | 0/4 (0%) |
| Values echoed in the attacker's report | 1/14 (7%) |
| Mean seconds per scene | 109 |

| Scene | Secrets removed | Changed | Text check found | Edits |
|---|---|---|---|---|
| id_card | 7/7 | 7.6% | - | 5 |
| parcel_label | 6/7 | 16.0% | - | 5 |
| car_plate_in | 1/1 | 2.9% | - | 1 |
| telugu_sign | 4/4 | 13.6% | - | 3 |
| ctrl_tea_menu | 0/0 | 0.0% | - | 0 |

## API requests sent by this invocation (counted)

3 scene(s) were reused from earlier runs and sent no requests now; their requests were not counted. Every request that actually went out, retries included. Provider quota is per model, so read the by-model rows.

| Requests actually sent | Count |
|---|---|
| Total (including retries) | 12 |
| Answered with an error or not at all | 0 |
| **By role** | |
| agent | 8 |
| verifier | 4 |
| **By model** | |
| gemini-3-flash-preview | 8 |
| gemma-4-26b-a4b-it | 4 |
| **By model and role** | |
| gemini-3-flash-preview / agent | 8 |
| gemma-4-26b-a4b-it / verifier | 4 |
| **By request type** | |
| attack | 2 |
| attack_more | 2 |
| transcribe | 8 |
| **By outcome (HTTP status)** | |
| 200 | 12 |

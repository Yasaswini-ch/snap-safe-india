# Indian benchmark results (2026-10-31, REGION=global, model gemini-3-flash-preview)

3 scenes scored (3 leak, 0 control), 2 errors. 15 planted secrets were legible in the originals and are the ground truth below.

The scenes are rendered, not photographed, and every value is fictional. One run each: the attacker samples.

| Metric | Result |
|---|---|
| Planted secrets removed | 14/15 (93%) |
| Scenes with every secret removed | 2/3 (67%) |
| Share of the frame changed (mean) | 8.8% |
| Leak scenes flagged (worst exposure specific or exact) | 3/3 (100%) |
| Control scenes falsely flagged | n/a |
| Text check found the expected kinds | 0/3 (0%) |
| Values echoed in the attacker's report | 0/10 (0%) |
| Mean seconds per scene | 123 |

| Scene | Secrets removed | Changed | Text check found | Edits |
|---|---|---|---|---|
| id_card | 7/7 | 7.6% | - | 5 |
| parcel_label | 6/7 | 16.0% | - | 5 |
| car_plate_in | 1/1 | 2.9% | - | 1 |
| telugu_sign | error: RateLimitError: Error code: 429 - [{'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/g | | | |
| ctrl_tea_menu | error: RateLimitError: Error code: 429 - [{'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/g | | | |

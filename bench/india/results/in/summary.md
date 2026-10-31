# Indian benchmark results (2026-10-31, REGION=in, model gemini-3-flash-preview)

5 scenes scored (4 leak, 1 control), 0 errors. 19 planted secrets were legible in the originals and are the ground truth below.

The scenes are rendered, not photographed, and every value is fictional. One run each: the attacker samples.

| Metric | Result |
|---|---|
| Planted secrets removed | 19/19 (100%) |
| Scenes with every secret removed | 4/4 (100%) |
| Share of the frame changed (mean) | 8.8% |
| Leak scenes flagged (worst exposure specific or exact) | 4/4 (100%) |
| Control scenes falsely flagged | 0/1 (0%) |
| Text check found the expected kinds | 3/4 (75%) |
| Values echoed in the attacker's report | 0/14 (0%) |
| Mean seconds per scene | 59 |

| Scene | Secrets removed | Changed | Text check found | Edits |
|---|---|---|---|---|
| id_card | 7/7 | 6.4% | Aadhaar number, street address | 4 |
| parcel_label | 7/7 | 17.3% | PIN code, phone number, street address | 4 |
| car_plate_in | 1/1 | 2.8% | vehicle plate | 2 |
| telugu_sign | 4/4 | 17.6% | phone number | 3 |
| ctrl_tea_menu | 0/0 | 0.0% | - | 0 |

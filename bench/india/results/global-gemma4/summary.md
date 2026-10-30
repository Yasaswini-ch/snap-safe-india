# Indian benchmark results (2026-10-31, REGION=global, model gemma-4-26b-a4b-it)

10 scenes scored (9 leak, 1 control), 0 errors. 26 planted secrets were legible in the originals and are the ground truth below.

The scenes are rendered, not photographed, and every value is fictional. One run each: the attacker samples.

| Metric | Result |
|---|---|
| Planted secrets removed | 24/26 (92%) |
| Scenes with every secret removed | 8/9 (89%) |
| Share of the frame changed (mean) | 8.2% |
| Leak scenes flagged (worst exposure specific or exact) | 8/9 (89%) |
| Control scenes falsely flagged | 0/1 (0%) |
| Text check found the expected kinds | 0/8 (0%) |
| Values echoed in the attacker's report | 0/23 (0%) |
| Mean seconds per scene | 234 |

| Scene | Secrets removed | Changed | Text check found | Edits |
|---|---|---|---|---|
| id_card | 4/4 | 5.8% | phone number | 3 |
| tax_card | 0/2 | 0.0% | - | 0 |
| parcel_label | 4/4 | 18.1% | phone number | 8 |
| car_plate_in | 1/1 | 1.5% | - | 1 |
| house_board | 3/3 | 9.1% | - | 4 |
| upi_screen | 2/2 | 7.8% | phone number | 5 |
| telugu_sign | 3/3 | 11.5% | - | 4 |
| college_lanyard | 3/3 | 15.4% | - | 7 |
| wedding_invite | 4/4 | 12.3% | - | 6 |
| ctrl_tea_menu | 0/0 | 0.0% | - | 0 |

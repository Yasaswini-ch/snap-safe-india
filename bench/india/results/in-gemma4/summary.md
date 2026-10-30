# Indian benchmark results (2026-10-31, REGION=in, model gemma-4-26b-a4b-it)

10 scenes scored (9 leak, 1 control), 0 errors. 26 planted secrets were legible in the originals and are the ground truth below.

The scenes are rendered, not photographed, and every value is fictional. One run each: the attacker samples.

| Metric | Result |
|---|---|
| Planted secrets removed | 26/26 (100%) |
| Scenes with every secret removed | 9/9 (100%) |
| Share of the frame changed (mean) | 7.0% |
| Leak scenes flagged (worst exposure specific or exact) | 9/9 (100%) |
| Control scenes falsely flagged | 0/1 (0%) |
| Text check found the expected kinds | 8/8 (100%) |
| Values echoed in the attacker's report | 0/23 (0%) |
| Mean seconds per scene | 252 |

| Scene | Secrets removed | Changed | Text check found | Edits |
|---|---|---|---|---|
| id_card | 4/4 | 7.9% | Aadhaar number, PIN code, street address | 4 |
| tax_card | 2/2 | 4.8% | PAN number | 3 |
| parcel_label | 4/4 | 9.2% | Aadhaar number, PIN code, phone number, street address | 4 |
| car_plate_in | 1/1 | 3.1% | vehicle plate | 1 |
| house_board | 3/3 | 8.2% | street address | 5 |
| upi_screen | 2/2 | 9.6% | Aadhaar number, UPI ID | 6 |
| telugu_sign | 3/3 | 8.1% | phone number | 3 |
| college_lanyard | 3/3 | 11.6% | - | 4 |
| wedding_invite | 4/4 | 8.0% | phone number, street address | 4 |
| ctrl_tea_menu | 0/0 | 0.0% | - | 0 |

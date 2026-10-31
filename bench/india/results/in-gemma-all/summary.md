# Indian benchmark results (2026-10-31, REGION=in-gemma-all, model gemma-4-26b-a4b-it)

10 scenes scored (9 leak, 1 control), 0 errors. 48 planted secrets were legible in the originals and are the ground truth below.

The scenes are rendered, not photographed, and every value is fictional. One run each: the attacker samples.

| Metric | Result |
|---|---|
| Planted secrets removed | 47/48 (98%) |
| Scenes with every secret removed | 8/9 (89%) |
| Share of the frame changed (mean) | 6.7% |
| Leak scenes flagged (worst exposure specific or exact) | 9/9 (100%) |
| Control scenes falsely flagged | 0/1 (0%) |
| Text check found the expected kinds | 8/8 (100%) |
| Values echoed in the attacker's report | 2/34 (6%) |
| Mean seconds per scene | 200 |

| Scene | Secrets removed | Changed | Text check found | Edits |
|---|---|---|---|---|
| id_card | 7/7 | 5.9% | Aadhaar number, PIN code, street address | 4 |
| tax_card | 5/5 | 5.2% | PAN number | 3 |
| parcel_label | 7/7 | 16.1% | PIN code, phone number, street address | 11 |
| car_plate_in | 1/1 | 1.3% | vehicle plate | 1 |
| house_board | 5/6 | 6.8% | street address | 4 |
| upi_screen | 4/4 | 5.5% | UPI ID | 4 |
| telugu_sign | 4/4 | 11.0% | phone number | 4 |
| college_lanyard | 6/6 | 8.1% | - | 4 |
| wedding_invite | 8/8 | 7.5% | phone number, street address | 5 |
| ctrl_tea_menu | 0/0 | 0.0% | - | 0 |

## API requests sent by this invocation (counted)

Every request that actually went out, retries included. Provider quota is per model, so read the by-model rows.

| Requests actually sent | Count |
|---|---|
| Total (including retries) | 10 |
| Answered with an error or not at all | 4 |
| **By role** | |
| agent | 6 |
| verifier | 4 |
| **By model** | |
| gemma-4-26b-a4b-it | 10 |
| **By model and role** | |
| gemma-4-26b-a4b-it / agent | 6 |
| gemma-4-26b-a4b-it / verifier | 4 |
| **By request type** | |
| attack | 1 |
| attack_more | 1 |
| transcribe | 8 |
| **By outcome (HTTP status)** | |
| 200 | 6 |
| 500 | 4 |

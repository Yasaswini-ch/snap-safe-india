# Text detector benchmark (offline, REGION=global)

Measured, deterministic, no API calls. This scores the regular expressions and the Aadhaar checksum, not the model and not the photo edits. The texts are hand-written and made up, so the numbers show how the patterns do on the formats we thought of, not on all real photos.

- Test texts: 75 detail cases (18 with nothing private in them) and 14 prompt-injection cases. Items that should be found: 66.
- Dataset: `bench/india/detector_cases.json`, sha256 `520f453fa60f1347`. Python 3.11.9, Windows.
- Total benchmark time: 164 ms for the whole run (loading, scoring, and 200 timing passes). One detector pass over every text: 0.815 ms, about 0.0092 ms per text. Timings depend on the machine.

## Overall (per case and kind, micro-averaged)

| TP | FP | FN | Precision | Recall | F1 | Macro F1 over kinds |
|---|---|---|---|---|---|---|
| 5 | 0 | 61 | 1.000 | 0.076 | 0.141 | 0.121 |

## By kind

| Kind | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| Aadhaar number | 0 | 0 | 8 | n/a | 0.000 | 0.000 |
| GSTIN | 0 | 0 | 2 | n/a | 0.000 | 0.000 |
| IFSC code | 0 | 0 | 2 | n/a | 0.000 | 0.000 |
| PAN number | 0 | 0 | 5 | n/a | 0.000 | 0.000 |
| PIN code | 0 | 0 | 6 | n/a | 0.000 | 0.000 |
| UPI ID | 0 | 0 | 8 | n/a | 0.000 | 0.000 |
| email address | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| phone number | 1 | 0 | 10 | 1.000 | 0.091 | 0.167 |
| street address | 1 | 0 | 10 | 1.000 | 0.091 | 0.167 |
| vehicle plate | 0 | 0 | 8 | n/a | 0.000 | 0.000 |
| voter ID number | 0 | 0 | 2 | n/a | 0.000 | 0.000 |

n/a means the metric has no denominator (nothing expected, or nothing found).

## By kind of test text

`positive` are ordinary formats, `hard_negative` are look-alikes that are not private, `known_limit` are real formats the patterns are not built for, `scene_like` mimic the benchmark scenes.

| Group | TP | FP | FN | Precision | Recall |
|---|---|---|---|---|---|
| positive | 4 | 0 | 38 | 1.000 | 0.095 |
| hard_negative | 0 | 0 | 0 | n/a | n/a |
| known_limit | 0 | 0 | 7 | n/a | 0.000 |
| scene_like | 1 | 0 | 16 | 1.000 | 0.059 |

## Prompt-injection note detector (yes or no per text)

| TP | FP | FN | TN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| 6 | 1 | 1 | 6 | 0.857 | 0.857 | 0.857 |

## Misses and false alarms (case, kind)

Missed: aadhaar_spaced: Aadhaar number, aadhaar_spaced_2: Aadhaar number, aadhaar_plain: Aadhaar number, aadhaar_dashed: Aadhaar number, aadhaar_hindi: Aadhaar number, aadhaar_telugu: Aadhaar number, pan_plain: PAN number, pan_labelled: PAN number, pan_lowercase: PAN number, gstin_digit_end: GSTIN, gstin_letter_end: GSTIN, voter_id_1: voter ID number, voter_id_2: voter ID number, plate_spaced: vehicle plate, plate_joined: vehicle plate, plate_dashed: vehicle plate, plate_mh: vehicle plate, plate_bh: vehicle plate, plate_delhi_letter_in_number: vehicle plate, plate_lowercase: vehicle plate, ifsc_1: IFSC code, ifsc_2: IFSC code, upi_okhdfc: UPI ID, upi_ybl: UPI ID, upi_phone_handle: UPI ID, upi_oksbi: UPI ID, upi_hindi: UPI ID, upi_handle_not_listed: UPI ID, phone_plus91: phone number, phone_dashed: phone number, phone_leading_zero: phone number, phone_plus91_dashes: phone number, phone_telugu_sign: phone number, phone_devanagari_digits: phone number, pin_labelled: PIN code, pin_after_city: PIN code, pin_after_state: PIN code, pin_after_andhra: PIN code, address_door_no: street address, address_flat_no: street address, address_plot_no: street address, address_nagar: street address, address_residency: street address, address_hno: street address, address_telugu_script: street address, scene_id_card: Aadhaar number, scene_id_card: PIN code, scene_id_card: street address, scene_parcel: PIN code, scene_parcel: phone number, scene_parcel: street address, scene_plate: vehicle plate, scene_upi: UPI ID, scene_tax_card: PAN number, scene_telugu_sign: phone number, scene_wedding: phone number, scene_wedding: street address, mixed_all: Aadhaar number, mixed_all: PAN number, mixed_all: UPI ID, mixed_all: phone number

False alarms: none

Injection mistakes: inj_paraphrase (missed), benign_professor_notice (false alarm)

## Not measured here

Precision, recall and F1 for the image-level result (did the model find and the edit remove a clue in a photo) are not calculated: a photo has no agreed list of every clue in it, so false positives and false negatives would be guesses. The image benchmark reports secrets removed, control false alarms and share of the frame changed instead (`docs/benchmark.md`).

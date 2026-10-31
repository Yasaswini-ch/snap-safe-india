# Text detector benchmark (offline, REGION=in)

Measured, deterministic, no API calls. This scores the regular expressions and the Aadhaar checksum, not the model and not the photo edits. The texts are hand-written and made up, so the numbers show how the patterns do on the formats we thought of, not on all real photos.

- Test texts: 75 detail cases (18 with nothing private in them) and 14 prompt-injection cases. Items that should be found: 66.
- Dataset: `bench/india/detector_cases.json`, sha256 `520f453fa60f1347`. Python 3.11.9, Windows.
- Total benchmark time: 443 ms for the whole run (loading, scoring, and 200 timing passes). One detector pass over every text: 2.197 ms, about 0.0247 ms per text. Timings depend on the machine.

## Overall (per case and kind, micro-averaged)

| TP | FP | FN | Precision | Recall | F1 | Macro F1 over kinds |
|---|---|---|---|---|---|---|
| 59 | 4 | 7 | 0.937 | 0.894 | 0.915 | 0.898 |

## By kind

| Kind | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| Aadhaar number | 8 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| GSTIN | 1 | 0 | 1 | 1.000 | 0.500 | 0.667 |
| IFSC code | 2 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| PAN number | 4 | 0 | 1 | 1.000 | 0.800 | 0.889 |
| PIN code | 6 | 1 | 0 | 0.857 | 1.000 | 0.923 |
| UPI ID | 7 | 0 | 1 | 1.000 | 0.875 | 0.933 |
| email address | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| phone number | 10 | 0 | 1 | 1.000 | 0.909 | 0.952 |
| street address | 10 | 1 | 1 | 0.909 | 0.909 | 0.909 |
| vehicle plate | 6 | 1 | 2 | 0.857 | 0.750 | 0.800 |
| voter ID number | 2 | 1 | 0 | 0.667 | 1.000 | 0.800 |

n/a means the metric has no denominator (nothing expected, or nothing found).

## By kind of test text

`positive` are ordinary formats, `hard_negative` are look-alikes that are not private, `known_limit` are real formats the patterns are not built for, `scene_like` mimic the benchmark scenes.

| Group | TP | FP | FN | Precision | Recall |
|---|---|---|---|---|---|
| positive | 42 | 0 | 0 | 1.000 | 1.000 |
| hard_negative | 0 | 4 | 0 | 0.000 | n/a |
| known_limit | 0 | 0 | 7 | n/a | 0.000 |
| scene_like | 17 | 0 | 0 | 1.000 | 1.000 |

## Prompt-injection note detector (yes or no per text)

| TP | FP | FN | TN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| 6 | 1 | 1 | 6 | 0.857 | 0.857 | 0.857 |

## Misses and false alarms (case, kind)

Missed: pan_lowercase: PAN number, gstin_letter_end: GSTIN, plate_delhi_letter_in_number: vehicle plate, plate_lowercase: vehicle plate, upi_handle_not_listed: UPI ID, phone_devanagari_digits: phone number, address_telugu_script: street address

False alarms: invoice_number_lookalike: voter ID number, batch_code_lookalike: vehicle plate, reference_dash_six_digits: PIN code, address_word_in_sale_text: street address

Injection mistakes: inj_paraphrase (missed), benign_professor_notice (false alarm)

## Not measured here

Precision, recall and F1 for the image-level result (did the model find and the edit remove a clue in a photo) are not calculated: a photo has no agreed list of every clue in it, so false positives and false negatives would be guesses. The image benchmark reports secrets removed, control false alarms and share of the frame changed instead (`docs/benchmark.md`).

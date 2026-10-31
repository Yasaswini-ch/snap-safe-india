# Submission text

Text for the event form. Only the demo video line and the access code still need filling in.

## Title

Snap Safe India

## One line

A photo privacy agent for India: it finds what a stranger could use in your photo, hides only that, and checks again.

## Description

People in India post photos with Aadhaar and PAN numbers, number plates, UPI IDs, courier labels and house name boards in
the picture, and a stranger can use every one of them. Snap Safe India looks at a photo the way a stranger would, finds
those clues, plans the fewest edits that hide them, makes the edits, and attacks the result again to check. It never prints
the names, addresses or numbers it finds, not even to the person who uploaded the photo.

The India detection recognizes Aadhaar numbers (with the checksum, so a tracking number is not mistaken for one), PAN, GSTIN
and voter ID numbers, number plates including the BH series, UPI IDs, IFSC codes, Indian mobile numbers, PIN codes and
address words such as "Door No." and "Nagar". Notes in a photo that tell an AI to report nothing are caught in English,
Hindi and Telugu. The report can be written in English, Telugu or Hindi. India is one region pack among several, so adding
a country is one file, and a US pack is included. It works from a web page or a Telegram bot.

## What we built, and what it grew out of

We built the India detection and checksum, the region packs, the Hindi and Telugu note detection, the English, Telugu and
Hindi reports, box snapping, request pacing with an optional second model for the re-checks, an Indian benchmark with a
scorer, a new interface, and the Telegram bot. The attack, plan, edit and re-attack loop and the image pipeline come from
the MIT-licensed project before-you-post by WhorideChicken, which we adapted and rebuilt for India.

## Tools used

- Gemini 3 Flash through Google AI Studio, to find the clues in a photo
- Gemma 4 (open weights), as a free option
- Python, FastAPI, OpenCV, Pillow and NumPy for the agent and the edits
- Telegram Bot API, Render, GitHub

## Results

On five rendered Indian scenes with planted fictional secrets (Gemini 3 Flash, one run each), the agent removed 19 of 19
secrets, changed 8.8% of each photo on average, and left the control photo untouched. An earlier run of the same scenes removed
only 11 of 19 and left a PIN code readable while the agent called the photo safe; we added a final literal check, and the two scenes that
had failed passed on rerun. With the India pack switched off, the same agent removed 18 of 19 secrets on the five scenes, against 19 of 19 with it on;
that is one secret in one run, so it is not proof the pack matters. The scenes are rendered, not photographed, every
value in them is made up, and two of the five results are from before that check was added. See [benchmark.md](benchmark.md).

## Limits

- "Verified" is the agent's own re-check, not proof.
- Edits are pixelation and inpainting, which look rougher than generative edits, and the boxes are sometimes larger than
  they need to be.
- A check takes one to a few minutes, mostly waiting on the model's rate limit.
- The photo is sent to Google's model to find the clues, so use made-up photos when trying it.
- The report can be written in Telugu or Hindi. Offline tests cover the language plumbing, and one live run each on the made-up ID card gave reports in the right script with no planted value in them; no native Telugu or Hindi reader has reviewed them, and only the report prose changes language. Among Indian-language photos only a Telugu sign has been tested; Hindi and Tamil photos have not.
- The pack-off and pack-on runs for two scenes come from different code versions, so that comparison is not clean.

## Links

- Code: github.com/Yasaswini-ch/snap-safe-india
- Live site: snap-safe-india.onrender.com, access code [ask the team]
- Demo video: [optional]

## Screenshots to attach

- The before and after slider on the home page
- "The agent at work" with the ID-card sample finished
- The benchmark section
- A report in Telugu, and the Telegram chat (`docs/img/telegram-*`)

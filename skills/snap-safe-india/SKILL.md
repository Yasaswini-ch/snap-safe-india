---
name: snap-safe-india
description: Check a photo for what a stranger could learn about the person who took it (Aadhaar, PAN, number plates, UPI IDs, addresses, labels, names) and get back a cleaned copy plus an honest report. Use before sharing, posting or sending a photo from India, or whenever a task involves hiding personal details in an image.
---

# Snap Safe India

An open-source privacy harness for photos, built around an open-weight vision model (Gemma 4 by default). The model finds the
clues; the harness plans the fewest edits that hide them, edits only inside those boxes, attacks the result again, and says
honestly whether anything specific is left. Code and docs: https://github.com/Yasaswini-ch/snap-safe-india (MIT).

## When to use it

- A user is about to post, send or publish a photo and wants to know what it gives away.
- A photo may show an ID card, number plate, courier label, house name board, UPI screen, a name, a phone number or a PIN code.
- The text may be in English, Telugu, Hindi or Tamil.

Do not use it for faces (the agent pixelates them, but does not identify anyone), for real identity documents of other people, or as a
guarantee: "Verified" is the agent's own re-check.

## Rules for the agent calling it

1. **Ask before sending a photo.** In a live run the photo goes to the model's host (Google's Gemini API by default). Tell the user, and
   prefer made-up or already-public photos for tests.
2. **Never repeat the values it hides.** The report names categories and how precisely something is exposed, not the names, numbers or
   addresses. Do not read them out of the original photo and put them in your reply either.
3. **Show the user the cleaned picture and the verdict.** Quote the verdict as written, including when it says the copy is not verified.
4. Use the cleaned PNG, not the original. It has no EXIF or GPS data.

## Calling the web service

`POST /api/run` as multipart form data, answered with a stream of JSON lines (NDJSON).

| Field | Meaning |
|---|---|
| `photos` | one to twenty image files (JPEG, PNG or WebP, up to 20 MB each); several are checked together as one account |
| `private` | `true` (the live mode) |
| `lang` | report language: `en`, `te` or `hi` |
| `style` | how hidden text is covered: `pixelate` (default) or `clean` (the colour around it, where that is plain) |
| `caption` | optional text the user will post with the photo; it is checked too |
| `code` | the access code, only if the server sets one |

Events, one JSON object per line: `start`, `status`, `attack` (the exposure graph and a summary), `textcheck`, `plan`, `edits`,
`outlines`, `preview`, `caption`, and last `done`. `done` carries `images` (base64 PNGs, one per photo), `before` and `after` (the
exposure level per category, 0 to 4), `hidden` (what was edited, each with a `label`), `safe`, `leftover`, `unverified` and `doubt`. A run takes
one to four minutes. Errors come as an `error` event or an HTTP status (403 wrong code, 413 too large, 429 run limit).

Other routes: `GET /api/status` (is a model configured, which one), `GET /api/samples` and `GET /api/sample/{name}` (recorded runs that
cost nothing and need no key).

## Using it from Python

```python
import base64, functools
from app import agent, meta, pipeline

img, _ = pipeline.load_image(open("photo.jpg", "rb").read())
events = agent.run([img], attack=functools.partial(meta.attack, private=True, lang="en"), private=True,
                   read=functools.partial(meta.read_text, private=True), style="clean")
done = [e for e in events if e["type"] == "done"][0]
open("safe-copy.png", "wb").write(base64.b64decode(done["images"][0]))
```

It needs `OPEN_API_BASE`, `OPEN_MODEL` and `OPEN_API_KEY` (or several keys in `OPEN_API_KEYS`) in the environment; any
OpenAI-compatible model with image input works. Gemma 4 (`gemma-4-26b-a4b-it`) and Gemini 3 Flash have been tested.

## Also available

A Telegram bot (`python -m app.telegram_bot`) and a WhatsApp webhook (`docs/whatsapp.md`) wrap the same agent. Region packs in
`app/regions` add ID formats for other countries, one file each (`docs/adding-a-country.md`).

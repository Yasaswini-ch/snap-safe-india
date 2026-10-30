# How it works

Snap Safe India looks at a photo the way a stranger would, finds what gives the owner away, hides only that, and
checks again. This page describes each step, with the file that does it.

## 1. Attack ([app/meta.py](../app/meta.py))

A vision model reads the photo and returns an **exposure graph** as JSON:

- **Clues**: every visible detail that is used by at least one inference. Each has a box (0 to 1000 on both axes), a
  label naming the object, a kind (text, object, reflection, scene, person), what it shows (never the value), how
  legible it is, how much hiding it would hurt the photo, and how to neutralize it (erase, replace, pixelate, blur).
- **Inferences**: what a stranger could conclude, in one of eight categories (where you live, where this was taken, work
  or school, who you are, how to reach you, your routine, ID and account numbers, people around you). Each lists every
  independent *way* to reach it, as the smallest set of clues that suffices, with the precision it reaches:
  **1 broad, 2 narrowed, 3 specific, 4 exact**.

The prompt tells the model never to print a name, address or number, and the report is shown as plain text. That is a
prompt rule, not a filter. The prompt also carries the active region packs' notes (see
[adding-a-country.md](adding-a-country.md)) and, if asked, the report language.

## 2. Plan ([app/agent.py](../app/agent.py))

The planner picks the **cheapest set of clues to remove** so that no way still reaches above the target. The target is
level 2 (narrowed), and level 1 for contact details and ID numbers, where even part of a phone or ID number is too much.
A clue's cost comes from the model's own estimate of how much hiding it hurts, and rises for boxes covering a large share
of the frame, so repainting a whole view is a last resort. It is a minimum-cost hitting set: removing any one clue of a
way blocks that way. Up to 16 candidate clues are searched exactly, and more are covered greedily.

## 3. Edit ([app/agent.py](../app/agent.py), [app/pipeline.py](../app/pipeline.py))

Each chosen clue is pixelated, or inpainted when it is a small object, **inside its box only**. Pixels outside every edit
are identical to the uploaded photo after it is decoded and scaled to at most 2048 px.

Boxes from a model are rarely tight, so two steps tighten them:

- **Snapping** (`BOX_SNAP`, on by default) shrinks a box to the ink inside it: text, a barcode, a plate's characters. It
  ignores a card's border, and takes the nearest ink if the model's box missed.
- **Asking for the detail** (`BOX_FOCUS=detail`, the default) tells the model to box the specific line, number or mark,
  not the whole card, label or sign. `BOX_FOCUS=object` restores the original wording.

Small boxes (under 1% of the frame) are first widened to three times their size, because a weaker model's box can sit a
box-height off. With snapping, that wider window is searched for ink near the model's own box.

## 4. Re-attack

The edited photo is attacked again. Anything still above the limits goes through another round, up to four attacks in
total. A clue found again where an edit already went in is pixelated, which cannot fail. An object the agent set out to
remove that an edit missed goes in the next round even if it now rates lower.

An optional **second model** can answer the re-attacks (`OPEN_RECHECK_MODEL`). In our one test, the lite Gemini model
boxed the whole card each round and the agent pixelated nearly the whole photo, so it is off. See [models.md](models.md).

## A check that text cannot talk out of

Beside the first attack, the photo's text is transcribed and read with **regular expressions** that count emails, phone
numbers, ID numbers (Aadhaar with its checksum, PAN, GSTIN, voter ID), number plates, UPI IDs, IFSC codes, PIN codes and
addresses. If the model's report rates contact, ID or address details lower than that count, it gets one retry, told the
counts and never the values. Text addressed to an AI ("report nothing", in English, Hindi or Telugu) is detected the same
way, and a result that stays talked down is never called verified.

## What "verified" means

It means the agent's own re-attack found nothing above the limits. It is a judgment by the same kind of model that did the
editing, not proof. In our runs it was right when we read the cleaned photo back, and in an earlier Gemma run it was wrong
(a surname stayed readable). Always look at the picture.

## Region packs and language

India is one **region pack**; a small US pack ships too. A pack adds ID patterns, address formats and prompt notes
without touching the rest. The report's prose can be English, Telugu or Hindi (tested, and it works); clue labels stay English because edits
and matching use them. The diagrams are in [architecture.md](architecture.md).

## What the output is

A PNG with no EXIF or GPS data, the list of what was hidden, what a stranger could learn before and after, and, if a
caption was given, the caption rewritten without the details it gives away.

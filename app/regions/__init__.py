"""Region packs. What gives a person away in a photo depends on the country: which ID numbers exist, how an address is
written, what a number plate looks like. Each pack is one file in this folder that exposes:

    NAME     shown in the README and the logs
    IDS      {kind: compiled regex}   ID and payment numbers; read first, each kind's matches blanked before the next
    ID_KINDS tuple of the kinds in IDS that a report must rate high when the text check reads them
    EXTRA    {kind: compiled regex}   other counted details (a postal code)
    PHONE    regex source or ""       phone formats the generic pattern misses
    ADDRESS  regex source or ""       address words and formats the generic pattern misses
    NOTE     text added to the attacker prompt: what to look for in photos from there

To add a country: copy india.py, change the patterns and the note, add it to PACKS below, and keep its self-check
(`python -m app.regions.<file>`) passing. Turn packs on with REGION=in,us. REGION=global uses none; the default is in.
"""
import os

from . import india, us

PACKS = {"in": india, "us": us}


def active(spec: str | None = None) -> list:
    spec = os.environ.get("REGION", "in") if spec is None else spec
    codes = [c.strip().lower() for c in spec.split(",") if c.strip()]
    unknown = [c for c in codes if c != "global" and c not in PACKS]
    if unknown:
        raise ValueError(f"Unknown REGION {unknown}: use global or any of {sorted(PACKS)}, comma separated")
    return [PACKS[c] for c in codes if c in PACKS]


def _join(parts) -> str:
    return "|".join(p for p in parts if p)


_packs = active()
NAMES = [p.NAME for p in _packs]
IDS = {k: v for p in _packs for k, v in p.IDS.items()}
ID_KINDS = tuple(k for p in _packs for k in p.ID_KINDS)
EXTRA = {k: v for p in _packs for k, v in p.EXTRA.items()}
PHONE = _join(p.PHONE for p in _packs)
ADDRESS = _join(p.ADDRESS for p in _packs)
NOTE = "".join(p.NOTE for p in _packs)

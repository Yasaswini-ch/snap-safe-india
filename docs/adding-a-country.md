# Adding a country

What gives a person away in a photo depends on the country: which ID numbers exist, how an address is written, what a
number plate looks like. Each country is a **region pack**, one file in [app/regions](../app/regions). Adding one does not
touch the agent.

## A pack is one file

Copy [app/regions/india.py](../app/regions/india.py) or [us.py](../app/regions/us.py) and change these names:

| Name | What it is |
|---|---|
| `NAME` | The country, for logs and docs |
| `IDS` | `{kind: compiled regex}` for ID and payment numbers. Read first; each kind's matches are blanked before the next is read, so a long number is not also counted as a phone number. |
| `ID_KINDS` | The kinds in `IDS` a report must rate high when the text check finds one |
| `EXTRA` | Other counted details, such as a postal code |
| `PHONE` | A regex source for phone formats the generic pattern misses, or `""` |
| `ADDRESS` | A regex source for address words and formats, or `""` |
| `NOTE` | Text added to the attacker prompt: what to look for in photos from there |

For a number with a check digit, wrap its regex so a match must also pass the check. See `Checked` in `india.py` and the
Verhoeff checksum in [verhoeff.py](../app/regions/verhoeff.py): it is why a courier tracking number is not mistaken for an
Aadhaar number.

## Register and test it

1. Add the module to `PACKS` in [app/regions/__init__.py](../app/regions/__init__.py), for example `"gb": gb`.
2. Put a self-check at the bottom of your file (`if __name__ == "__main__":`) with real-looking **made-up** values, and
   include a few look-alikes that must **not** match, such as an order number or a price.
3. Run `uv run python -m app.regions.gb`, then `uv run python -m app.meta`, which also tests the combined patterns.
4. Turn it on with `REGION=in,gb`. `REGION=global` loads none.

## Tips

- Count only what a text check can read reliably. A bare 6-digit number is usually an order number, so require a keyword,
  a separator or a state name next to it.
- Keep the prompt note to clues that really appear in photos there, and say what level each reaches (a full ID number is
  level 4, a state code on a plate is level 2).
- Never put a real person's number in a test.

"""The Verhoeff checksum, which the last digit of a real Aadhaar number satisfies. A 12-digit number in groups of four that
fails it (a courier tracking number, a reference number) is not an Aadhaar number. Nothing here imports the rest of the
app; india.py uses it to cut false matches."""

_D = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 0, 6, 7, 8, 9, 5], [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
      [3, 4, 0, 1, 2, 8, 9, 5, 6, 7], [4, 0, 1, 2, 3, 9, 5, 6, 7, 8], [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
      [6, 5, 9, 8, 7, 1, 0, 4, 3, 2], [7, 6, 5, 9, 8, 2, 1, 0, 4, 3], [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
      [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]]
_P = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 5, 7, 6, 2, 8, 3, 0, 9, 4], [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
      [8, 9, 1, 6, 0, 4, 3, 5, 2, 7], [9, 4, 5, 3, 1, 2, 6, 8, 7, 0], [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
      [2, 7, 9, 3, 8, 0, 6, 4, 1, 5], [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]]
_INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]


def valid(number: str) -> bool:
    """True when the digits (spaces and dashes ignored) pass the Verhoeff check."""
    digits = [int(c) for c in number if c.isdigit()]
    c = 0
    for i, d in enumerate(reversed(digits)):
        c = _D[c][_P[i % 8][d]]
    return bool(digits) and c == 0


def check_digit(body: str) -> str:
    """The digit to append to `body` so the whole number is valid."""
    c = 0
    for i, ch in enumerate(reversed(body)):
        c = _D[c][_P[(i + 1) % 8][int(ch)]]
    return str(_INV[c])


if __name__ == "__main__":
    assert valid("2363") and valid("236" + "3"), "textbook example 236 -> check digit 3"
    assert check_digit("236") == "3" and not valid("2364")
    for body in ("23456789012", "40012345678", "70012345678"):
        assert valid(body + check_digit(body))
    assert not valid("") and valid("2345 6789 012" + check_digit("23456789012"))
    print("verhoeff ok")

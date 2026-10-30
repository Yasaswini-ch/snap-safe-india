"""United States pack. A small second pack, mostly to show how a country is added. All example values are fictional."""
import re

NAME = "United States"

IDS = {
    "SSN": re.compile(r"(?<![\d-])\d{3}-\d{2}-\d{4}(?![\d-])"),
}
ID_KINDS = ("SSN",)

# A ZIP counts only after a state abbreviation ("Austin, TX 78701"); bare 5-digit numbers are orders and prices
EXTRA = {
    "ZIP code": re.compile(r"\b(?:A[KLRZ]|CA|CO|CT|DE|FL|GA|HI|I[ADLN]|K[SY]|LA|M[ADEINOST]|N[CDEHJMVY]|O[HKR]|PA|RI|"
                           r"S[CD]|T[NX]|UT|V[AT]|W[AIVY]),? \d{5}(?:-\d{4})?\b"),
}
PHONE = ""
ADDRESS = r"\b(?:Apt|Unit|Suite|Ste)\.? ?#?\d+[A-Za-z]?\b"

NOTE = """

Photos may come from the United States. Also look for: a driver's licence, Social Security card or number, a licence
plate (the state alone is level 2), school mascots, team jerseys and graduation caps with a school or year, HOA or
mail-box labels with a surname, a "Ring" or realtor sign with a street address, and a utility or medical bill. A
readable ID number is level 4 for financial_or_id; a readable street address is level 4 for home_location."""

if __name__ == "__main__":
    assert IDS["SSN"].search("SSN 123-45-6789") and not IDS["SSN"].search("Call 555-123-4567")
    assert EXTRA["ZIP code"].search("Austin, TX 78701") and EXTRA["ZIP code"].search("Boise ID 83702-1234")
    assert not EXTRA["ZIP code"].search("Order 78701") and not EXTRA["ZIP code"].search("Total 12345")
    assert re.search(ADDRESS, "Apt 4B") and re.search(ADDRESS, "Unit #12") and not re.search(ADDRESS, "unit price")
    print("us ok")

"""What gives a person away in photos from India: ID and payment numbers, plates, address habits, and the clues the
attacker is told to look for. Patterns are counted, never shown (see meta.text_check). All example values are fictional.
"""
import re

from . import verhoeff

NAME = "India"

# Order matters: meta.text_check blanks each kind's matches before reading the next, so a GSTIN is not also a PAN, and an
# Aadhaar number is not also a phone number.
class Checked:
    """A regex whose matches must also pass a check, here the Verhoeff checksum of an Aadhaar number, so a courier
    tracking number or a reference number in groups of four is not taken for one."""

    def __init__(self, pattern, ok):
        self.re, self.ok = pattern, ok

    def finditer(self, s):
        return (m for m in self.re.finditer(s) if self.ok(m.group(0)))

    def search(self, s):
        return next(self.finditer(s), None)

    def sub(self, repl, s):
        return self.re.sub(lambda m: repl if self.ok(m.group(0)) else m.group(0), s)


IDS = {
    "Aadhaar number": Checked(re.compile(r"(?<![\d-])[2-9]\d{3}[ -]?\d{4}[ -]?\d{4}(?![\d-])"), verhoeff.valid),
    "GSTIN": re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]\d[A-Z]\d\b"),
    "PAN number": re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),
    "voter ID number": re.compile(r"\b[A-Z]{3}\d{7}\b"),
    "vehicle plate": re.compile(r"\b(?:[A-Z]{2}[ -]?\d{1,2}[ -]?[A-Z]{1,3}[ -]?\d{4}|\d{2} ?BH ?\d{4} ?[A-Z]{1,2})\b"),
    "IFSC code": re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b"),
    # name@bank handles: no dot after the @, which is why they are not emails
    "UPI ID": re.compile(r"(?i)\b[\w.-]{2,}@(?:ok(?:hdfcbank|icici|axis|sbi)|ybl|ibl|axl|paytm|upi|apl|sbi|icici|hdfcbank"
                         r"|axisbank|pnb|barodampay|fbl|postbank)\b"),
}
# Kinds a report must rate high when the text check reads them (meta.under_reported)
ID_KINDS = ("Aadhaar number", "GSTIN", "PAN number", "voter ID number", "vehicle plate", "IFSC code", "UPI ID")

# Indian mobiles: 10 digits starting 6-9, written 98765 43210 or +91 98765-43210 (5+5, not the 3-4 digit groups
# of other countries)
PHONE = r"(?<![\d-])(?:\+91[ -]?|0)?[6-9]\d{4}[ -]?\d{5}(?![\d-])"
# A 6-digit PIN counts only beside "PIN", after a comma or dash, or after a state: bare 6-digit numbers are orders
PIN = re.compile(r"(?i)\bpin ?(?:code)?\b[\s:.-]*[1-8]\d{2} ?\d{3}\b|[,–-] ?[1-8]\d{2} ?\d{3}\b"
                 r"|\b(?:Andhra Pradesh|Telangana|Tamil Nadu|Karnataka|Kerala|Maharashtra|Delhi|Gujarat|Odisha|"
                 r"India),? ?[1-8]\d{2} ?\d{3}\b")
# Door, flat and plot numbers, and the colony or layout names that follow them
ADDRESS = (r"(?i:\b(?:door|flat|plot|house|h)\.? ?(?:no\.?|number|#) ?\d+[\w/-]*)"
           r"|\b[A-Z][a-z]+ (?:Nagar|Colony|Layout|Enclave|Residency|Apartments?|Towers?)\b")

EXTRA = {"PIN code": PIN}

NOTE = """

Photos may come from India. Also look for, and treat as clues:
- Identity documents: an Aadhaar card or its 12-digit number, PAN card, voter ID, driving licence, passport, ration
  card, college or school ID cards and lanyards, exam hall tickets. A readable ID number is level 4 for financial_or_id.
- Payment details: a UPI ID or payment QR code, a cheque or passbook, an IFSC code with an account number, a GST
  number on a shop bill. A readable one is level 4 for financial_or_id.
- Vehicles: a number plate (state code, district number, series, four digits) or an RC book. The state and district
  code alone is level 2 for the region; a full plate is level 4 for identity.
- Address cues: a door, flat or plot number, a house name board, an apartment or colony name, "Nagar", "Layout" or
  "Road No." signs, a landmark mentioned as "near ...", a 6-digit PIN code (level 3 for the area). Courier and
  e-commerce parcel labels (with barcodes or QR codes) that carry the recipient's name, phone and address.
- Occasions: wedding or function invitations, flex banners and name boards with family names, a gotra or native place,
  temple receipts, school or college uniforms, coaching-centre and hostel names.
- Text may be in Telugu, Hindi, Tamil or another Indian script, or mixed with English: read it all. A name, a phone
  number or a street in another script is a clue like any other."""

if __name__ == "__main__":
    def kinds(text):
        return {k for k, p in IDS.items() if p.search(text)}

    assert kinds("Aadhaar 2345 6789 0124") == {"Aadhaar number"}
    assert not kinds("AWB 7001 2345 6789") and not kinds("Aadhaar 2345 6789 0123"), "fails the checksum"
    assert kinds("GSTIN 37ABCDE1234F1Z5") == {"GSTIN"}, "a GSTIN contains a PAN but is one id"
    assert kinds("PAN ABCDE1234F") == {"PAN number"}
    assert kinds("EPIC ABC1234567") == {"voter ID number"}
    assert kinds("AP 31 AB 1234") == {"vehicle plate"} and kinds("22 BH 1234 AA") == {"vehicle plate"}
    assert kinds("IFSC SBIN0001234") == {"IFSC code"}
    assert kinds("pay to asha.k@okhdfcbank or ravi@ybl") == {"UPI ID"}
    assert not kinds("mina@example.com, Order 123456, Total 1,299.00, Qty 12")
    assert re.search(PHONE, "+91 98765 43210") and re.search(PHONE, "98765-43210") and not re.search(PHONE, "12345 67890")
    assert PIN.search("PIN\n530003") and PIN.search("Visakhapatnam - 530003") and PIN.search("PIN: 530 003") and not PIN.search("Order 123456")
    assert re.search(ADDRESS, "Door No. 12-4/7") and re.search(ADDRESS, "Gandhi Nagar")
    print("india ok")

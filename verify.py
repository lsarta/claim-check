"""
claim-check: verify that every claim is backed by a saved source.

Claude reads the saved sources in captures/ and writes claims into claims.json.
This script trusts none of it. For every claim it checks, in order:

  1. the capture the claim points to is listed in sources.json
  2. the capture file exists and its SHA-256 fingerprint still matches
  3. the quote appears in the capture word for word (spacing, curly vs straight
     quotes, and dash styles are ignored; everything else must match)
  4. the claimed value appears inside that quote

A claim that passes every check is "verified". A claim that fails any check is
"held", along with the reason. Results go to REPORT.md.

Usage:
  python3 verify.py                      check claims.json, write REPORT.md
  python3 verify.py fetch <id> <url> [--from TEXT] [--to TEXT]
      Save a web page's text into captures/ (optional, needs internet).
      --from keeps text starting at the first TEXT; --to stops just before the
      first TEXT after that. Use them to keep the release body and drop menus.
  python3 verify.py paste <id> <title> <url> [file]
      Save text you copied from a page into captures/ (works offline). Reads the
      file if given, otherwise whatever is typed or piped in.

fetch and paste never overwrite: if <id> is already used, they stop and say so.

Python standard library only. Nothing here calls an AI model.
"""

import datetime
import hashlib
import html.parser
import json
import re
import sys
import urllib.request
from decimal import Decimal, InvalidOperation
from pathlib import Path

HERE = Path(__file__).parent
SOURCES = HERE / "sources.json"
CLAIMS = HERE / "claims.json"
CAPTURES = HERE / "captures"
REPORT = HERE / "REPORT.md"


# ---------------------------------------------------------------- helpers

def sha256_of(path):
    """A fingerprint of the file. Change one character and it changes completely."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def squash_spaces(text):
    """Turn every run of spaces, tabs, and newlines into a single space."""
    return re.sub(r"\s+", " ", text).strip()


# Typographic characters that look alike on screen, mapped to their plain keyboard versions.
LOOKALIKES = str.maketrans({
    "\u2018": "'", "\u2019": "'", "\u201a": "'", "\u201b": "'",   # curly single quotes / apostrophes
    "\u201c": '"', "\u201d": '"', "\u201e": '"', "\u201f": '"',   # curly double quotes
    "\u2013": "-", "\u2014": "-",                                   # en dash, em dash
    "\u00a0": " ", "\u202f": " ",                                   # non-breaking spaces
})


def normalize(text):
    """Make text comparable: plain quotes and hyphens, and single spaces.
    Used on both the quote and the capture, so neither side gets special treatment."""
    return squash_spaces(text.translate(LOOKALIKES))


def to_number(text):
    """Turn '$1,234.5', '4.3%', or '250,000 jobs' into Decimal('1234.5') etc.
    Returns None if there is no number in it."""
    match = re.search(r"-?\d[\d,]*(?:\.\d+)?", str(text))
    if not match:
        return None
    try:
        return Decimal(match.group().replace(",", ""))
    except InvalidOperation:
        return None


def numbers_in(text):
    """Every number written in the text, with commas, $, % and unit words ignored."""
    return [to_number(n) for n in re.findall(r"\d[\d,]*(?:\.\d+)?", text)]


# ---------------------------------------------------------------- the checks

def check_claim(claim, sources):
    """Return ("verified", "") or ("held", "the specific reason")."""
    capture_id = claim.get("capture_id", "")
    quote = claim.get("quote", "")
    value = claim.get("value", "")

    # 1. Is the capture one we know about?
    source = sources.get(capture_id)
    if source is None:
        return "held", f"capture ID '{capture_id}' is not listed in sources.json"

    # 2. Is the file there, and unchanged since it was saved?
    path = HERE / source["file"]
    if not path.exists():
        return "held", f"capture file {source['file']} is missing"
    if sha256_of(path) != source["sha256"]:
        return "held", f"{source['file']} has changed since it was saved (SHA-256 mismatch)"

    # 3. Does the quote appear in the capture, word for word?
    if not quote.strip():
        return "held", "claim has no quote"
    capture_text = normalize(path.read_text(encoding="utf-8"))
    if normalize(quote) not in capture_text:
        return "held", "quote does not appear word for word in the capture"

    # 4. Does the claimed value appear inside the quote?
    wanted = to_number(value)
    if wanted is None:
        return "held", f"value '{value}' is not a number"
    if abs(wanted) not in numbers_in(quote):
        return "held", f"value {value} does not appear in the quote"

    return "verified", ""


# ---------------------------------------------------------------- the report

def cell(text):
    """Make text safe to put inside a Markdown table cell."""
    return str(text).replace("|", "\\|").replace("\n", " ")


def write_report(rows):
    verified = sum(1 for _, status, _ in rows if status == "verified")
    lines = [
        "# Claim check report",
        "",
        f"{verified} of {len(rows)} claims verified, {len(rows) - verified} held.",
        "Generated by `python3 verify.py`. Do not edit by hand.",
        "",
        "| Claim | What | Value | Unit | Capture | Status | Reason |",
        "|---|---|---|---|---|---|---|",
    ]
    for claim, status, reason in rows:
        lines.append("| " + " | ".join(cell(x) for x in [
            claim.get("claim_id", "?"), claim.get("subject", ""),
            claim.get("value", ""), claim.get("unit", ""), claim.get("capture_id", "?"),
            "✅ verified" if status == "verified" else "⛔ held", reason or "",
        ]) + " |")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return verified


def run_checks():
    sources = {s["id"]: s for s in json.loads(SOURCES.read_text(encoding="utf-8"))}
    claims = json.loads(CLAIMS.read_text(encoding="utf-8"))
    rows = [(claim, *check_claim(claim, sources)) for claim in claims]
    verified = write_report(rows)
    print(f"{len(rows)} claims: {verified} verified, {len(rows) - verified} held. See REPORT.md.")


# ---------------------------------------------------------------- adding a new source

def id_taken(capture_id):
    """True (with a message) if this capture ID is already in use. Saved captures are never replaced."""
    known = {s["id"] for s in json.loads(SOURCES.read_text(encoding="utf-8"))}
    if capture_id in known or (CAPTURES / f"{capture_id}.txt").exists():
        print(f"Capture ID '{capture_id}' already exists. Saved captures are never overwritten.")
        print("Nothing was saved. Choose a new ID, for example "
              f"'{capture_id}-v2'.")
        return True
    return False


def save_capture(capture_id, text, details):
    """Write the capture file, then record it, with its fingerprint, in sources.json."""
    path = CAPTURES / f"{capture_id}.txt"
    CAPTURES.mkdir(exist_ok=True)
    path.write_text(text, encoding="utf-8")
    sources = json.loads(SOURCES.read_text(encoding="utf-8"))
    sources.append({"id": capture_id, **details, "file": f"captures/{capture_id}.txt",
                    "captured_on": datetime.date.today().isoformat(), "sha256": sha256_of(path)})
    SOURCES.write_text(json.dumps(sources, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Saved {path.relative_to(HERE)} and added '{capture_id}' to sources.json.")


def paste(capture_id, title, url, file=None):
    """Save text a person copied from a page. No internet needed."""
    if id_taken(capture_id):
        return 1
    if file:
        if not Path(file).is_file():
            print(f"File not found: {file}. Nothing was saved.")
            return 1
        text = Path(file).read_text(encoding="utf-8-sig")
    else:
        if sys.stdin.isatty():
            print("Paste the text, then press Enter and Ctrl-D (Ctrl-Z then Enter on Windows).")
        text = sys.stdin.read()
    if not text.strip():
        print("No text was given. Nothing was saved.")
        return 1
    save_capture(capture_id, text if text.endswith("\n") else text + "\n",
                 {"title": title, "url": url, "method": "pasted"})
    return 0

class TextOnly(html.parser.HTMLParser):
    """Collect the readable text of a web page, skipping scripts, styles, and menus."""
    SKIP = {"script", "style", "nav", "header", "footer", "noscript", "svg"}
    BREAKS = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "table", "section"}

    def __init__(self):
        super().__init__()
        self.parts, self.skipping, self.title, self.tag = [], 0, "", ""

    def handle_starttag(self, tag, attrs):
        self.tag = tag
        if tag in self.SKIP:
            self.skipping += 1
        elif tag in self.BREAKS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skipping:
            self.skipping -= 1
        elif tag in self.BREAKS:
            self.parts.append("\n")

    def handle_data(self, data):
        if self.tag == "title" and not self.title:
            self.title = squash_spaces(data)  # the page's own title, for sources.json
        if not self.skipping:
            self.parts.append(data)


def fetch(capture_id, url, start=None, stop=None):
    """Download a page, save its text to captures/<id>.txt, and record it in sources.json.
    If start/stop markers are given, keep only the text between them."""
    if id_taken(capture_id):
        return 1
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "claim-check/1.0"})
        with urllib.request.urlopen(request, timeout=20) as response:
            page = response.read().decode("utf-8-sig", errors="replace")
    except Exception as error:  # no internet, blocked site, bad URL...
        print(f"Could not fetch {url}: {error}")
        print("Nothing was saved. The sample captures still work offline.")
        return 1

    parser = TextOnly()
    parser.feed(page)
    lines = [squash_spaces(line) for line in "".join(parser.parts).splitlines()]
    text = "\n".join(line for line in lines if line) + "\n"

    # Trim to the body of the document, if markers were given. Fail rather than guess.
    if start:
        if start not in text:
            print(f"--from text not found on the page: {start!r}. Nothing was saved.")
            return 1
        text = text[text.index(start):]
    if stop:
        if stop not in text:
            print(f"--to text not found on the page: {stop!r}. Nothing was saved.")
            return 1
        text = text[:text.index(stop)].rstrip() + "\n"

    # kept_from / kept_to are the trim markers, so anyone can re-save it the same way.
    save_capture(capture_id, text, {"title": parser.title, "url": url, "method": "fetched",
                                    "kept_from": start, "kept_to": stop})
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["fetch"] and len(args) in (3, 5, 7):
        options = dict(zip(args[3::2], args[4::2]))  # {"--from": "...", "--to": "..."}
        if set(options) <= {"--from", "--to"}:
            sys.exit(fetch(args[1], args[2], options.get("--from"), options.get("--to")))
        print(__doc__)
        sys.exit(2)
    elif args[:1] == ["paste"] and len(args) in (4, 5):
        sys.exit(paste(*args[1:]))
    elif len(sys.argv) == 1:
        run_checks()
    else:
        print(__doc__)
        sys.exit(2)

# Instructions for Claude

This repo teaches one rule: **a fact only counts if a plain script can find it in a saved source.**
Your job is to extract claims. `verify.py` decides whether they count. Do not try to do its job.

## Extracting claims

When asked to extract facts, read the files in `captures/` and add entries to `claims.json`.
Every claim has exactly these fields:

```json
{
  "claim_id": "c9",
  "capture_id": "bea-income-2026-08",
  "subject": "U.S. personal saving rate, August 2026",
  "value": "4.1",
  "unit": "percent",
  "quote": "the personal saving rate—personal saving as a percentage of DPI—was 4.1 percent."
}
```

- `capture_id`: the `id` of the capture in `sources.json` that the quote comes from.
- `subject`: a short plain-English label for what the number measures.
- `value`: the number only, written as it appears in the quote. No words.
- `unit`: what the number counts (percent, billion dollars, votes, jobs...).
- `quote`: a span copied **verbatim** from the capture that contains the value.

## Rules

1. **Never paraphrase a quote.** Copy it character for character, including dashes, curly
   apostrophes, and odd punctuation. Only line breaks and extra spaces may differ.
2. **Never edit, reformat, or "clean up" a file in `captures/`.** The SHA-256 fingerprint in
   `sources.json` will stop matching and every claim from that capture will be held.
   The one exception is a tamper test (see below).
3. **Never change `sha256` in `sources.json`** to make a check pass.
4. One claim per number. Keep quotes short: one sentence or less is ideal.
5. If you cannot find a quote that contains the number, do not add the claim. Say so instead.
6. Use a new `claim_id` for each claim. Do not reuse or renumber existing IDs.

## After extracting

Run `python3 verify.py` and show the summary line. If any claim is held, report the reason.
Do not "fix" a held claim by loosening the quote or editing `verify.py`. A held claim is the
system working. Fix it only by finding the true verbatim quote, or remove the claim.

## Adding a source

Always save a new source through `verify.py`, which records its fingerprint. Never create or write a
file in `captures/` directly, and never reuse an existing capture ID (the commands refuse to overwrite).

- **From the web:** `python3 verify.py fetch <new-id> <url> --from "..." --to "..."`. Choose markers
  so the capture is the body of the document only: no site menus, social links, or staff contact
  details. This needs internet access and may fail; if it does, say so and suggest the person paste
  the text instead.
- **Pasted by the person:** when someone gives you text copied from a page, save it with
  `python3 verify.py paste <new-id> "<title>" <url>`, passing their text on standard input exactly as
  given (for example with a quoted heredoc, `<<'END_OF_CAPTURE'`). Do not tidy, trim, or reword it.
  Ask for the page title and address if they weren't given. If the text includes menus or staff contact
  details, ask whether they want to paste only the body before saving.

## Tamper test

If the person explicitly asks for a tamper test (or to change a capture to see what happens):
change one word in the capture they name (or pick one), run `python3 verify.py`, and show the result.
Then restore the capture exactly (for example `git checkout -- captures/<file>`), run the checker again,
and confirm the results are back to normal. Never change `sha256` in `sources.json` during a tamper test.

## Undo

If the person asks to undo their changes: put `claims.json`, `sources.json`, and `captures/` back the way
they were in the repo's first commit (`git rev-list --max-parents=0 HEAD`), delete every capture file that
isn't in that commit (committed or not), and run `python3 verify.py` so `REPORT.md` matches. Show the
person what was removed, and the final summary line.

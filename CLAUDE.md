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
3. **Never change `sha256` in `sources.json`** to make a check pass.
4. One claim per number. Keep quotes short: one sentence or less is ideal.
5. If you cannot find a quote that contains the number, do not add the claim. Say so instead.
6. Use a new `claim_id` for each claim. Do not reuse or renumber existing IDs.

## After extracting

Run `python3 verify.py` and show the summary line. If any claim is held, report the reason.
Do not "fix" a held claim by loosening the quote or editing `verify.py`. A held claim is the
system working. Fix it only by finding the true verbatim quote, or remove the claim.

## Adding a source

`python3 verify.py fetch <new-id> <url> --from "..." --to "..."` saves a page's text into `captures/`
and records its fingerprint. Choose `--from`/`--to` so the capture is the body of the document only:
no site menus, social links, or staff contact details. This needs internet access and may fail;
if it does, say so and continue with the existing captures. Never write a capture file by hand.

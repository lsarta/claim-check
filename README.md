# claim-check

Claude reads saved copies of public documents and writes down facts it finds, each with the exact sentence it came from.
A plain Python script, with no AI in it, then checks every fact against the saved copy and marks it **verified** or **held**, with the reason.

**What "verified" means:** the quote is really in the source, and the number is really in the quote. It does not mean the claim is the right fact.
For example, a claim that July's trade deficit was $71.2 billion would pass, because June's $71.2 billion figure is in the same sentence as July's.
The checker catches invented quotes and numbers; a person still has to check that the label fits.

## Run it

1. On this repo's GitHub page, click **Use this template** → **Create a new repository** to make your own copy.
2. Go to [claude.ai/code](https://claude.ai/code), connect your GitHub account if asked, and pick your copy.
3. Ask Claude: *"Run the checker and show me the report."*

You'll see 8 claims: 7 verified and 1 held. No API keys, no installs, no internet needed.

**The held claim is on purpose.** `c8` says the U.S. trade deficit grew 24.4 percent in July 2026. That number is real; it's in the source.
But the quote was reworded instead of copied, so the checker can't find it in the source, and the claim doesn't count.
That's the whole idea: a right number with made-up wording is still held.

## Things to try

Ask Claude:

- *"Extract three more numbers from the trade capture and run the checker."*
- *"Run a tamper test: change one word in a capture and run the checker."* Every claim from that capture is held, because the saved file no longer matches its fingerprint. Claude puts the file back afterwards.
- *"Undo your changes and run the checker again."* This removes added claims and new captures and puts everything back to how the template started.

## What's in here

| File | What it is |
|---|---|
| `captures/` | Saved text of three U.S. government releases (Federal Reserve, BEA). Never edited after saving. |
| `sources.json` | Each capture's title, web address, how it was saved, the date, and its SHA-256 fingerprint (a code that changes if even one character of the file changes). |
| `claims.json` | Facts extracted from the captures: value, unit, the exact quote, and which capture. |
| `verify.py` | The checker. About 290 lines, Python standard library only. |
| `REPORT.md` | The output: one row per claim, verified or held. |
| `CLAUDE.md` | The rules Claude follows in this repo. |

For each claim, `verify.py` checks that the capture exists and its fingerprint still matches,
that the quote appears in the capture word for word, and that the value appears inside the quote.
When comparing quotes it ignores spacing, curly vs straight quotes, and dash styles. Every word and number must still match.

## Exercises

1. **Add a source.** Ask Claude to fetch a public page, such as a BEA, Census, or Federal Reserve news release, and save just the body of the release. If fetching doesn't work (web sessions often have limited internet access, and some sites block scripts), copy the release text from your browser, paste it to Claude with the page's title and address, and ask Claude to save it as a new capture. Then ask Claude to extract claims from it.
2. **Add a staleness check.** Each source has a `captured_on` date. Hold any claim whose capture is older than, say, 90 days, with the reason "capture is stale".
3. **Add a review step for held claims.** Write held claims to a `review.json` file where a person can mark each one `accept` or `reject` with a note. Make `verify.py` show accepted ones as "verified by reviewer" without loosening the automatic checks.
4. **Add a chart of verified values.** Generate a `chart.svg` (or a Markdown bar chart made of `█` characters) showing only verified claims. Held claims never appear on the chart.

## Notes

- Captures are saved as the body of each release, not the full web page. Site navigation, social links, and staff contact details were trimmed off; one leftover "Share" button label remains at the top of the Federal Reserve capture.
- The captures are U.S. federal government works and are in the public domain. They were saved on 2026-10-03; the agencies' live pages may since have changed. That's the point of saving them.
- Saving a capture never overwrites an existing one. If the ID is already used, the command stops and says so.

### Running it in a local terminal instead

With Python 3.9 or newer: `python3 verify.py` runs the checker and rewrites `REPORT.md`.
To add sources: `python3 verify.py fetch <id> <url> --from "first words" --to "words just after the end"`,
or `python3 verify.py paste <id> "<title>" <url> [file]` (reads the file, or text you paste in).
To undo changes: `git checkout -- . && git clean -fd captures/`, then run the checker again.
On a Mac with Python from python.org, `fetch` may fail with a certificate error; run the `Install Certificates.command` that came with Python.

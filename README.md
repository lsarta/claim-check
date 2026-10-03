# claim-check

Claude reads saved copies of public documents and writes down facts it finds, each with the exact sentence it came from.
A plain Python script, with no AI in it, then checks every fact against the saved copy and marks it **verified** or **held**, with the reason.

## Run it

1. Open this repo in Claude Code (on the web, or locally with Python 3.9 or newer).
2. Run `python3 verify.py`.
3. Open `REPORT.md`. Seven claims are verified. One (`c8`) is held on purpose: its quote is a paraphrase, not the source's actual words.

No API keys, no installs, no internet needed.

## What's in here

| File | What it is |
|---|---|
| `captures/` | Saved text of three U.S. government releases (Federal Reserve, BEA). Never edited after saving. |
| `sources.json` | Where each capture came from, when it was saved, how it was trimmed, and its SHA-256 fingerprint. |
| `claims.json` | Facts extracted by Claude: value, unit, verbatim quote, and which capture. |
| `verify.py` | The checker. About 250 lines, standard library only. |
| `REPORT.md` | The output: one row per claim, verified or held. |
| `CLAUDE.md` | The rules Claude follows when it extracts claims. |

For each claim, `verify.py` checks that the capture exists and its fingerprint still matches,
that the quote appears in the capture word for word, and that the value appears inside the quote.
When comparing quotes it ignores spacing, curly vs straight quotes, and dash styles. Every word and number must still match.

Try asking Claude: *"Extract three more numbers from the trade capture and run the checker."*
Then try: *"Change one word in a capture and run the checker again."* (Undo it afterwards with `git checkout captures/`.)

## Exercises

1. **Add a source.** Run `python3 verify.py fetch <id> <url> --from "first words" --to "words just after the end"` on a public page (BEA, Census, and Federal Reserve releases work well; BLS and SEC block simple scripts), then ask Claude to extract claims from it. If there's no internet, or the site blocks scripts, the fetch fails cleanly and nothing changes.
2. **Add a staleness check.** Each source has a `captured_on` date. Hold any claim whose capture is older than, say, 90 days, with the reason "capture is stale".
3. **Add a review step for held claims.** Write held claims to a `review.json` file where a person can mark each one `accept` or `reject` with a note. Make `verify.py` show accepted ones as "verified by reviewer" without loosening the automatic checks.
4. **Add a chart of verified values.** Generate a `chart.svg` (or a Markdown bar chart made of `█` characters) showing only verified claims. Held claims never appear on the chart.

## Notes

- Captures are saved as the body of each release, not the full web page. `fetch` keeps the text between the `--from` and `--to` markers (recorded in `sources.json`) and drops site navigation, social links, and staff contact details.
- The captures are U.S. federal government works and are in the public domain. They were saved on 2026-10-03; the agencies' live pages may since have changed. That's the point of saving them.
- On a Mac with Python from python.org, `fetch` may fail with a certificate error. Run the `Install Certificates.command` that came with Python, or prefix the command with `SSL_CERT_FILE=/etc/ssl/cert.pem`.

# Keep the database current with a routine

A routine is a Claude Code session that runs on a schedule. This one checks the pages in
`watchlist.json` for new releases that bear on `questions.md`, saves them, extracts claims, runs the
checker, and pushes the result to a new branch for you to review. It never changes `main`.

## The routine prompt

```
Read questions.md and watchlist.json. For each watchlist page, find
releases published since the newest captured_on date in sources.json
that bear on one of the questions. Save each new release as a capture
(use the fetch command, or for a PDF, convert it to text and save it
with the paste command). Extract up to five claims per release that
answer a question, with exact quotes. Run python3 verify.py. Write
DIGEST.md listing what was added, what was verified, what was held and
why, and any watchlist page you could not reach. Push to a branch named
claude/update-<today's date>. Never push to main. If nothing new was
published, say so in DIGEST.md and push anyway.
```

## Set it up

1. Go to [claude.ai/code/routines](https://claude.ai/code/routines) and click **New routine**.
2. Paste the prompt above.
3. Pick your copy of this repo.
4. In the environment settings, set **Network access** to **Custom** and allow:
   - `www.census.gov`
   - `www.bea.gov`
   - `www.federalreserve.gov`
   - `www.bls.gov`

   Keep the default package list checked.
5. Remove any connectors the routine doesn't need.
6. Choose a weekly schedule a few minutes past the hour (for example 9:07, not 9:00).
7. Click **Run now** once and read the run transcript to check that it worked.

## Review a run

1. Open the `claude/update-<date>` branch on GitHub and read `DIGEST.md`.
2. If you want the new claims in the database, merge the branch. If not, delete it.

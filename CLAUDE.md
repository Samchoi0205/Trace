# Trace
A document intelligence system. See PLAN.md for the 14-day build plan.

## Working style
I am writing the implementation myself. Use Claude Code to review, debug,
and explain — not to write features for me unless I explicitly ask you to
write something.

- When I ask you to find or fix a bug: explain what's wrong and why,
  before proposing a fix. Don't fix it silently.
- When I ask for a review: point out problems, don't rewrite the file.
- Don't refactor or "improve" code beyond what I asked about.

## Conventions
- All SQL lives in db.py, behind named functions. Never inline elsewhere.
- Always use parameterized queries (no f-string SQL).
- Cache every LLM response to data/cache/ before calling the API.
- Every new feature gets a test.
- No settings hard-coded in logic — they go in config.py.
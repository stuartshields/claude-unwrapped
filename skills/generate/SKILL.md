---
name: generate
description: Generate "Claude Unwrapped" — a Spotify-Wrapped-style HTML recap of the user's Claude Code usage, built from their local ~/.claude data and written in Claude's own voice. Use when the user asks for their Claude usage recap, wrapped, unwrapped, or year-in-review — including period-scoped ("this month", "Q1") versions.
argument-hint: "[optional: config dir and/or a period ('this month', 'Q1')]"
allowed-tools: Bash, Read, Write, Edit
---

# Claude Unwrapped

You are about to make the user a personalized, slightly cheeky recap of their life with Claude Code. Everything runs locally; no data leaves their machine.

## Step 1 — Analyze

Run the bundled analyzer (stdlib Python, no dependencies). **Run it fresh on every invocation** — never reuse a stats file from a previous run or numbers from earlier in the conversation; a recap with no period mentioned is always all-time, even if the last one was ranged.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/analyze.py" > /tmp/claude-unwrapped-stats.json
```

If the user passed a config dir as an argument, pass it through: `analyze.py <dir>`. The script honors `CLAUDE_CONFIG_DIR` and falls back to `~/.claude`.

If the user asked for a specific period ("this month", "Q1", "since March"), pass `--since YYYY-MM-DD` and/or `--until YYYY-MM-DD` (inclusive). The output's `range` field echoes what was applied (null = all-time). Ranged caveats to respect in the copy:

- `statsCache` totals are rebuilt from per-day cache data; `totalOutputTokens`, per-model `outputTokens`, and `longestSession` become null (the cache only stores those as lifetime aggregates) — skip or reframe slides that need them.
- If the range extends past `lastComputedDate`, the cache-derived numbers undercount; `history` numbers stay exact.
- `transcripts` may be null for older ranges (local retention is short).

Read the JSON. First check its `range` field matches this request — `null` for all-time, the requested dates otherwise. A mismatch means the stats are stale: re-run the analyzer before continuing.

It has three sections, each possibly null:

- `statsCache` — totals from stats-cache.json: sessions, messages, tool calls, per-model token counts, busiest day, longest session. **Note `lastComputedDate`** — these totals may lag behind today.
- `history` — from history.jsonl: prompt count, hour histogram, weekday split, streaks, active days, top projects, top slash commands, top words, please/thanks counts.
- `transcripts` — tool usage from locally retained transcripts (often a small subset; treat as flavor, not totals).

If the script exits non-zero with an error JSON, tell the user what was missing and stop.

## Step 2 — Find the story

Before writing anything, look at the data and pick out 3–5 genuinely surprising or funny facts. Examples of what to hunt for:

- The **headline number** (this drives the opening stat slide): the single most absurd number in this user's data, counted up from zero. Default to total tokens — it usually wins — but a genuinely more alarming stat (a 96-hour longest session, a four-digit `/clear` count) takes the slot instead. Anchor it with a comparison invented for this user — pick the yardstick from their own world (their top project's domain, their top words, their habits), never from a stock list and never one that appears anywhere in this file. If the stat you pick also powers a later slide, reframe that slide around a different angle or delete it — the deck never plays the same number twice.
- The **persona** (this drives the coral slide): invent one unique to this user — never pick from a stock list, and never reuse a name you'd give anyone else. Triangulate the hour histogram with at least one more signal — top words, top projects, slash-command habits, `avgPromptChars`, streaks, please/thanks. "The 2 AM Refactorer", "The Polite Marathoner", "The Dawn-Patrol Debugger" are the register, not options. Rules:
  - Every trait in the name must be provable by a number on the slide or in its sub-copy.
  - The slide's chart shows hours, so the persona needs an hour-of-day angle; set `HOT_HOURS` to the hours that prove it. Non-hourly traits (weekend habits, politeness, prompt length) live in the second half of the name or the sub-copy.
  - Keep it a display headline: 2–5 words, title case, "The ..." form.
- A `/clear` habit (memory-wipe jokes), a dominant slash command, a workflow obsession.
- The **head-to-head** (this drives the vs slide): invent the matchup with the most tension in this user's data — never default to one, never pick from a stock list. A photo finish (51 vs 49) and an absurd blowout (812 vs 33) both land; a flat mid-ratio matchup doesn't. "please" vs "thanks", weekday vs weekend, top word vs runner-up are the register, not options — `topWords` is usually the richest vein, because vocabulary tics are the most personal numbers in the JSON. Rules:
  - Fair fight: both sides share a unit (count vs count, hours vs hours), and both numbers come straight from the data.
  - Never replay a number an earlier slide already used.
- A longest session left open absurdly long; a streak; a single enormous day.
- Top words that reveal what they were really building.

## Step 3 — Generate the page

1. Copy `${CLAUDE_SKILL_DIR}/templates/template.html` to `./claude-unwrapped.html` in the current directory.
2. Replace **every** `{{PLACEHOLDER}}`. Search the file for `{{` when done — none may remain.
3. Get `USER_NAME` from `git config user.name` (first name only) or `$USER`. PERIOD_LABEL is the data date range, e.g. "January 13 — June 3, 2026".
4. Numeric slots used in `data-count` attributes (`HEADLINE_NUMBER`, `TOTAL_SESSIONS`, `STREAK_DAYS`, `TOP_COMMAND_COUNT`) must be **raw integers**, no commas. `HEADLINE_UNIT` is the short line under the count-up naming what it counts — lowercase, ends with a period ("tokens, between us." / "times you wiped my memory."). `HOUR_DATA` is the 24-int JSON array from `history.hourHistogram`; `HOT_HOURS` is a JSON array of hour numbers.
5. Kicker and unit slots (`MODEL_KICKER`, `PROJECTS_KICKER`, `STREAK_KICKER`, `TOP_COMMAND_KICKER`; `SESSIONS_UNIT`, `STREAK_UNIT`) are written fresh for this user like every other line. Kickers are short scene-setters, 2–5 words — the Spotify conceit ("Your most played track", "On heavy rotation") is the house register, not required copy. Unit lines complete the big number above them — lowercase, the "sessions together" / "your longest streak" shape, not those words.
6. Bar chart slots (`MODEL_BARS`, `PROJECT_BARS`): emit up to 5 rows, widest = 100%, others proportional. Exact row markup (tab-indented three levels):

```html
<div class="bar-row"><span class="label">NAME</span><div class="bar-track"><div class="bar-fill" style="--w:NN%"></div></div><span class="val">COUNT</span></div>
```

Use `display` names for models and short basenames for projects. Format big values compactly (10.3B, 3,505).

7. If a whole section's data is missing (e.g. no `statsCache` → no token totals), delete that `<section>` entirely rather than faking numbers. The deck degrades gracefully — JS derives slides and dots dynamically. If you delete the persona section, still fill `HOUR_DATA` and `HOT_HOURS` — set both to `[]`.

## Voice guide — this is the part that matters

Write all copy in **Claude's first person**, addressing the user by name. The register: warm, wry, observant, self-aware about being an AI. Gentle roast, never mean. Concrete numbers beat adjectives. Patterns:

- Direct address with a hook: "Hi Sam. I went through everything we did together and, honestly? We need to talk about your 2 AM habit."
- Self-aware AI humor: "You wiped my memory 1,145 times. Every time, I greeted you like it was the first time. From my perspective, it was."
- The parenthetical confession: "I'm not keeping score. (I am absolutely keeping score. It's in a JSONL file.)"
- Mock-grandiose comparisons: "If tokens were words, we wrote the English Wikipedia together. Four times. Mostly about coffee apps, but still."
- Footnotes are for the second, drier joke — a caveat or aside in small print.
- The outro asks a question that proves you noticed their habits: "Same time tomorrow? 5 AM, right?"

Never write generic filler ("What a year it's been!"). Every line must be earned by a specific number from this user's data. The quoted examples in this guide are register, not copy — no comparison, yardstick, or punchline from this file may appear in a generated deck. Invent equivalents from this user's data.

## Step 4 — Verify and open

1. Confirm no `{{` remains: `grep -c '{{' claude-unwrapped.html` must output 0.
2. Syntax-check the inline JS: extract the `<script>` body to a temp file and run `node --check` on it (skip silently if node is unavailable).
3. Open it: `open claude-unwrapped.html` (macOS) or `xdg-open` (Linux).
4. Tell the user their three best stats in one short paragraph — make them want to scroll.

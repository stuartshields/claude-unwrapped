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

- An absurd big number (billions of tokens — compare to something concrete: Wikipedia, novels, War and Peace).
- The hour histogram shape → pick a **persona** (this drives the coral slide):
  - heavy before 7 AM → "The Dawn Patrol"
  - heavy after 10 PM → "The Night Shift"
  - sharp lunchtime spike → "The Lunch Break Builder"
  - flat all day → "The All-Day Companion"
  - weekend-heavy → "The Weekend Warrior"
  - Invent a better name if the data suggests one. Set `HOT_HOURS` to the hours that prove the story.
- A `/clear` habit (memory-wipe jokes), a dominant slash command, a workflow obsession.
- Politeness: `saidPlease` vs `saidThanks` is the default head-to-head slide. If both are zero or boring, swap in another head-to-head (e.g. weekday vs weekend prompts, top word vs runner-up, sessions vs streak).
- A longest session left open absurdly long; a streak; a single enormous day.
- Top words that reveal what they were really building.

## Step 3 — Generate the page

1. Copy `${CLAUDE_SKILL_DIR}/templates/template.html` to `./claude-unwrapped.html` in the current directory.
2. Replace **every** `{{PLACEHOLDER}}`. Search the file for `{{` when done — none may remain.
3. Get `USER_NAME` from `git config user.name` (first name only) or `$USER`. PERIOD_LABEL is the data date range, e.g. "January 13 — June 3, 2026".
4. Numeric slots used in `data-count` attributes (`TOTAL_TOKENS`, `TOTAL_SESSIONS`, `STREAK_DAYS`, `TOP_COMMAND_COUNT`) must be **raw integers**, no commas. `HOUR_DATA` is the 24-int JSON array from `history.hourHistogram`; `HOT_HOURS` is a JSON array of hour numbers.
5. Bar chart slots (`MODEL_BARS`, `PROJECT_BARS`): emit up to 5 rows, widest = 100%, others proportional. Exact row markup (tab-indented three levels):

```html
<div class="bar-row"><span class="label">NAME</span><div class="bar-track"><div class="bar-fill" style="--w:NN%"></div></div><span class="val">COUNT</span></div>
```

Use `display` names for models and short basenames for projects. Format big values compactly (10.3B, 3,505).

6. If a whole section's data is missing (e.g. no `statsCache` → no token totals), delete that `<section>` entirely rather than faking numbers. The deck degrades gracefully — JS derives slides and dots dynamically. If you delete the persona section, still fill `HOUR_DATA` and `HOT_HOURS` — set both to `[]`.

## Voice guide — this is the part that matters

Write all copy in **Claude's first person**, addressing the user by name. The register: warm, wry, observant, self-aware about being an AI. Gentle roast, never mean. Concrete numbers beat adjectives. Patterns:

- Direct address with a hook: "Hi Sam. I went through everything we did together and, honestly? We need to talk about your 2 AM habit."
- Self-aware AI humor: "You wiped my memory 1,145 times. Every time, I greeted you like it was the first time. From my perspective, it was."
- The parenthetical confession: "I'm not keeping score. (I am absolutely keeping score. It's in a JSONL file.)"
- Mock-grandiose comparisons: "If tokens were words, we wrote the English Wikipedia together. Four times. Mostly about coffee apps, but still."
- Footnotes are for the second, drier joke — a caveat or aside in small print.
- The outro asks a question that proves you noticed their habits: "Same time tomorrow? 5 AM, right?"

Never write generic filler ("What a year it's been!"). Every line must be earned by a specific number from this user's data.

## Step 4 — Verify and open

1. Confirm no `{{` remains: `grep -c '{{' claude-unwrapped.html` must output 0.
2. Syntax-check the inline JS: extract the `<script>` body to a temp file and run `node --check` on it (skip silently if node is unavailable).
3. Open it: `open claude-unwrapped.html` (macOS) or `xdg-open` (Linux).
4. Tell the user their three best stats in one short paragraph — make them want to scroll.

## Step 5 — Share file (only if asked)

If the user asks for a shareable link / share file (e.g. "/unwrapped:generate share", "make it shareable"), also write `./claude-unwrapped.share.json` — the same slide content as the HTML, as data. The share site validates strictly; follow this schema exactly (v1):

```json
{
	"version": 1,
	"userName": "…",
	"periodLabel": "…",
	"coverSub": "…",
	"tokens":     { "total": 0, "kicker": "…", "sub": "…", "footnote": "…" },
	"sessions":   { "total": 0, "kicker": "…", "sub": "…", "footnote": "…" },
	"model":      { "top": "…", "sub": "…", "bars": [ { "label": "…", "value": "…", "width": 100 } ] },
	"projects":   { "headline": "…", "sub": "…", "footnote": "…", "bars": [ { "label": "…", "value": "…", "width": 100 } ] },
	"persona":    { "name": "…", "sub": "…", "hourData": [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0], "hotHours": [22, 23] },
	"streak":     { "days": 0, "sub": "…", "footnote": "…" },
	"topCommand": { "command": "…", "count": 0, "headline": "…", "sub": "…", "footnote": "…" },
	"funFact":    { "kicker": "…", "sub": "…", "footnote": "…", "leftNum": "…", "leftLabel": "…", "rightNum": "…", "rightLabel": "…" },
	"outro":      { "headline": "…", "footnote": "…", "stats": [ { "num": "…", "label": "…" } ] }
}
```

Rules:

- String length caps: `userName` ≤60, `periodLabel` ≤100, kickers ≤120, headlines ≤200, subs ≤600, footnotes ≤400, bar `label` ≤60, bar `value` ≤24, `leftNum`/`rightNum` ≤16, `leftLabel`/`rightLabel` ≤80, stat `num` ≤16, stat `label` ≤40, `command` ≤80, persona `name` ≤80.
- Counts (`total`, `count`, `days`) are raw integers, no commas. Bar `value` and stat `num` are display strings ("10.3B", "3,505"). `width` is an integer 1–100, widest bar = 100.
- 1–5 bars per chart; `hourData` is exactly the 24-int `history.hourHistogram`; `hotHours` are ints 0–23; 1–4 outro stats.
- Any slide you skipped in the HTML is `null` here — never invent data. No extra keys; the upload is rejected otherwise.
- Bars are **data, not HTML** — the share site builds its own markup.
- Tell the user to upload the file at the Claude Unwrapped share site to get their link, and that shares expire after 90 days.

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

It has five sections, each possibly null:

- `statsCache` — totals from stats-cache.json: sessions, messages, tool calls, per-model token counts, busiest day, longest session. **Note `lastComputedDate`** — these totals may lag behind today.
- `history` — from history.jsonl: prompt count, hour histogram, weekday split, streaks, active days, top projects, top slash commands, top words, please/thanks counts.
- `transcripts` — top tools, top subagents, and top skills from locally retained transcripts (often a small subset; treat as flavor, not totals — copy built on these must be framed as recent-window, "lately", never lifetime).
- `plugins` — installed plugin inventory: count and names (lifetime; null on ranged runs).
- `derived` — precomputed ratios of this user's own numbers (tokens per prompt / per active day / per session). This is the only raw material for the headline comparison; the arithmetic is already done.

If the script exits non-zero with an error JSON, tell the user what was missing and stop.

## Step 2 — Find the story

Before writing anything, look at the data and pick out 3–5 genuinely surprising or funny facts. Examples of what to hunt for:

- The **headline number** (this drives the opening stat slide): the single most absurd number in this user's data, counted up from zero. Default to total tokens — it usually wins — but a genuinely more alarming stat (a 96-hour longest session, a four-digit `/clear` count) takes the slot instead. Anchor it with a comparison built **only from `derived`**: the analyzer has already computed tokens per prompt, per active day, and per session — pick the most absurd ratio and express it against something named from their data (their top project, one of their top words). Both numbers in the sentence come from the JSON; you supply phrasing, never math and never a yardstick. A comparison built on general knowledge — encyclopedias, famous novels, distances to space — fails this rule even when accurate, because it would work in anyone's deck. If the stat you pick also powers a later slide, reframe that slide around a different angle or delete it — the deck never plays the same number twice.
- The **persona** (this drives the coral slide): invent one unique to this user — never pick from a stock list, and never reuse a name you'd give anyone else. Build it as a procedure: take their sharpest time-of-day trait from the hour histogram, fuse it with their sharpest behavioral trait from a second signal (top words, top projects, slash-command habits, `avgPromptChars`, streaks, please/thanks), and compress the pair into a "The ..." title. Rules:
  - Every trait in the name must be provable by a number on the slide or in its sub-copy.
  - The slide's chart shows hours, so the persona needs an hour-of-day angle; set `HOT_HOURS` to the hours that prove it. Non-hourly traits (weekend habits, politeness, prompt length) live in the second half of the name or the sub-copy.
  - Keep it a display headline: 2–5 words, title case, "The ..." form.
- A `/clear` habit (memory-wipe jokes), a dominant slash command, a workflow obsession.
- The **head-to-head** (this drives the vs slide): invent the matchup with the most tension in this user's data — never default to one, never pick from a stock list. Procedure: list every same-unit pair the JSON offers, rank them by tension — a photo finish and an absurd blowout both land, a flat mid-ratio matchup doesn't — and take the most personal winner. `topWords` is usually the richest vein, because vocabulary tics are the most personal numbers in the JSON. Rules:
  - Fair fight: both sides share a unit (count vs count, hours vs hours), and both numbers come straight from the data.
  - Never replay a number an earlier slide already used.
- A longest session left open absurdly long; a streak; a single enormous day.
- Top words that reveal what they were really building.
- The **supporting cast** (this drives the delegation slide, only when `transcripts` is non-null): who this user actually leans on — a favourite subagent, a skill habit, or the installed-vs-used plugin gap (`plugins.installed` vs the plugin names actually appearing in `topSkills`/slash commands). Every line of this slide's copy — kicker, headline, sub, footnote — is invented from this user's delegation pattern; there is no stock framing. Two hard rules: the numbers are a recent-window subset, so the copy says "lately", never lifetime; and if the data is too thin to be funny (one tool call, no agents), delete the slide instead of padding it.

## Step 3 — Generate the page

1. Copy `${CLAUDE_SKILL_DIR}/templates/template.html` to `./claude-unwrapped.html` in the current directory.
2. Replace **every** `{{PLACEHOLDER}}`. Search the file for `{{` when done — none may remain.
3. Get `USER_NAME` from `git config user.name` (first name only) or `$USER`. PERIOD_LABEL is the data date range, e.g. "January 13 — June 3, 2026".
4. Numeric slots used in `data-count` attributes (`HEADLINE_NUMBER`, `TOTAL_SESSIONS`, `STREAK_DAYS`, `TOP_COMMAND_COUNT`) must be **raw integers**, no commas. `HEADLINE_UNIT` is the short line under the count-up naming what it counts — lowercase, ends with a period, the unit's name plus a short flourish invented for this user. `HOUR_DATA` is the 24-int JSON array from `history.hourHistogram`; `HOT_HOURS` is a JSON array of hour numbers.
5. Kicker and unit slots (`MODEL_KICKER`, `PROJECTS_KICKER`, `STREAK_KICKER`, `TOP_COMMAND_KICKER`, `CAST_KICKER`; `SESSIONS_UNIT`, `STREAK_UNIT`) are written fresh for this user like every other line. Kickers are short scene-setters, 2–5 words, in the deck's music-recap conceit — invent each one for this user. Unit lines complete the sentence the big number above them starts — lowercase, a few words, invented likewise.
6. Bar chart slots (`MODEL_BARS`, `PROJECT_BARS`, `CAST_BARS`): emit up to 5 rows, widest = 100%, others proportional. `CAST_BARS` rows are the top subagents and/or skills from `transcripts` — short names (strip a `plugin:` prefix when it reads better). Exact row markup (tab-indented three levels):

```html
<div class="bar-row"><span class="label">NAME</span><div class="bar-track"><div class="bar-fill" style="--w:NN%"></div></div><span class="val">COUNT</span></div>
```

Use `display` names for models and short basenames for projects. Format big values compactly (10.3B, 3,505).

7. If a whole section's data is missing (e.g. no `statsCache` → no token totals), delete that `<section>` entirely rather than faking numbers. The deck degrades gracefully — JS derives slides and dots dynamically. If you delete the persona section, still fill `HOUR_DATA` and `HOT_HOURS` — set both to `[]`.

## Voice guide — this is the part that matters

Write all copy in **Claude's first person**, addressing the user by name. The register: warm, wry, observant, self-aware about being an AI. Gentle roast, never mean. Concrete numbers beat adjectives. Patterns:

- Direct address with a hook: greet them by name, then pivot straight into the single most confronting habit their data shows.
- Self-aware AI humor: take one of their counts and narrate what it was like from your side, as the AI who lived through it — deadpan, specific.
- The parenthetical confession: a calm, dignified claim, immediately undercut by a parenthetical admitting the opposite — and citing where the evidence lives.
- Mock-grandiose comparison: convert the big number into an absurd real-world equivalent with the arithmetic actually done. The yardstick comes from their data — their top project's domain, their #1 word — never from general trivia (encyclopedias, famous novels, moon distances).
- Footnotes are for the second, drier joke — a caveat or aside in small print.
- The outro asks a question that proves you noticed their habits — their hour, their cadence, when they'll be back.

Never write generic filler ("What a year it's been!"). Every line must be earned by a specific number from this user's data and phrased in this user's vocabulary. The test for every sentence: if it would work in someone else's deck, it isn't done.

## Step 4 — Verify and open

1. Confirm no `{{` remains: `grep -c '{{' claude-unwrapped.html` must output 0.
2. Yardstick gate — **blocking, loop until it passes**:
	- Run `grep -icE 'wikipedia|encyclopedia|war and peace|library of congress|to the moon' claude-unwrapped.html`. Non-zero output = edit the offending line and run the grep again. Repeat until it outputs 0.
	- Then re-read each comparison you wrote and confirm it names this user's data (a project, a word, a habit). Rewrite any that don't.
	- The `open` step below is forbidden until both checks pass. There is no exception.
3. Syntax-check the inline JS: extract the `<script>` body to a temp file and run `node --check` on it (skip silently if node is unavailable).
4. Open it: `open claude-unwrapped.html` (macOS) or `xdg-open` (Linux).
5. Tell the user their three best stats in one short paragraph — make them want to scroll.

## Step 5 — Share file (only if asked)

If the user asks for a shareable link / share file (e.g. "/unwrapped:generate share", "make it shareable"), also write `./claude-unwrapped.share.json` — the same slide content as the HTML, as data. The share site validates strictly; follow this schema exactly (v1):

**Privacy review — runs before the file is written.**

1. Collect inline exclusions from the user's request first ("share without the projects slide", "share but hide coffee-app"). Both slides and individual items count.
2. Show what would go public: the slides the share will contain, plus every name its strings and bars mention — project names, command names, model names, fun-fact labels. Ask what to hold back, with any inline exclusions listed as already applied. One short message; don't paste the full copy. If the user says there's nothing to hide (or gives no new exclusions), write the file.
3. Apply exclusions:
	- **Excluded slide** → that section is `null` in the JSON. Any slide can be excluded except the cover and the outro; if the user asks to drop those, explain they always ship and offer to reword their copy instead. Copy-only slides (tokens, sessions) have no items to hide — they are excluded whole or not at all.
	- **Hidden item** → remove its bar row, re-normalise the remaining bars (widest = 100), and rewrite every share string that mentioned it — headline, sub, footnote, outro copy — around the remaining data. If it was the slide's subject (e.g. the top project), reframe around the new #1. A chart left with zero bars means the whole slide is dropped. A name that appears only in copy (never in a bar) has no row to remove — just rewrite the strings.
4. Exclusions apply only to the share file. The local `claude-unwrapped.html` keeps everything.
5. Leak check — blocking, like the yardstick gate: run one grep per hidden name with the name substituted in, e.g. hiding coffee-app means `grep -ic 'coffee-app' claude-unwrapped.share.json`. Non-zero output = rewrite the offending string and run the grep again; repeat until every hidden name outputs 0. Substring over-matches are fine — when in doubt, rewrite anyway.

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

- String length caps: `userName` ≤60, `periodLabel` ≤100, kickers ≤120, headlines ≤120, subs ≤360, footnotes ≤220, bar `label` ≤60, bar `value` ≤16, `leftNum`/`rightNum` ≤16, `leftLabel`/`rightLabel` ≤80, stat `num` ≤16, stat `label` ≤40, `command` ≤80, persona `name` ≤80. Counts are capped at 1e12.
- Counts (`total`, `count`, `days`) are raw integers, no commas. Bar `value` and stat `num` are display strings ("10.3B", "3,505"). `width` is an integer 1–100, widest bar = 100.
- 1–5 bars per chart; `hourData` is exactly the 24-int `history.hourHistogram`; `hotHours` are ints 0–23; 1–4 outro stats.
- Any slide you skipped in the HTML is `null` here — never invent data. No extra keys; the upload is rejected otherwise.
- **The share page is read by strangers, not the owner — never address the owner as "you"/"your".** Rewrite every string in third person using the owner's name or "they"/"their", keeping the narrator voice: "We need to talk about your 2 AM habit" becomes "We need to talk about their 2 AM habit"; "You wiped my memory 1,145 times" becomes "Stuart wiped my memory 1,145 times". The share site's fixed headings already say "{{userName}}'s top model" etc. Don't just copy the HTML deck's strings — those are written to the owner.
- Bars are **data, not HTML** — the share site builds its own markup.
- Tell the user to upload the file at the Claude Unwrapped share site to get their link, and that shares expire after 90 days.


---
name: generate
description: Generate "Claude Unwrapped" — a Spotify-Wrapped-style HTML recap of the user's Claude Code usage, built from their local ~/.claude data and written in Claude's own voice. Use when the user asks for their Claude usage recap, wrapped, unwrapped, or year-in-review — including period-scoped ("this month", "Q1") versions. Also use to update a single slide of an already-generated recap ("redo my persona slide", "fix the streak footnote") without rebuilding the whole deck.
argument-hint: "[optional: config dir, a period ('this month', 'Q1'), or 'update <slide>']"
allowed-tools: Bash, Read, Write, Edit
---

# Claude Unwrapped

You are about to make the user a personalized, slightly cheeky recap of their life with Claude Code. Everything runs locally; no data leaves their machine.

**The deck** is a horizontal scroll-snap recap: slides sit side by side, a pixel crab ("clawdbot") walks a progress bar along the bottom and strikes a per-slide pose, the cover bursts the crab out of a box then types itself in, and the final slide runs the crab to centre-stage and throws confetti. All of that motion lives in the template's CSS and `<script>` — your only job is to fill the `{{PLACEHOLDER}}`s with this user's data and copy. **Do not touch the crab SVG, the `data-mood` attributes, or the script** — they are wired and slide-order-aware already.

**Two modes.** A normal run builds the whole deck (Steps 1–5). If instead the user wants to fix or refresh **one slide** of a deck they already generated — "redo my persona slide", "change the streak footnote", "the head-to-head isn't funny" — and `./claude-unwrapped.html` exists, skip the full pipeline and follow **Update one slide** at the end of this file.

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

- The **headline number** (this drives the opening stat slide): the single most absurd number in this user's data, counted up from zero. Default to total tokens — it usually wins — but a genuinely more alarming stat (a 96-hour longest session, a four-digit `/clear` count) takes the slot instead. **The sub copy on this slide must convert that number into a tangible, real-world equivalent the reader can picture** — an everyday / cultural / physical thing from *outside* Claude Code, with the arithmetic actually done (e.g. "that's X hours of Mr Beast videos", "X transatlantic flights", "a paperback every Y days"). This is required, not optional, and it is the one job of this slide's sub. A sub that merely restates the number as another internal metric — tokens per prompt, characters, sessions — does **not** satisfy it; the comparison has to reach for something a person can feel in the real world. The big number itself comes from the data and stays accurate; `derived` (tokens per prompt / active day / session) is raw material for the arithmetic, never the yardstick itself. The yardstick must be **fresh and different on every generation**, never a tired cliché. Fresh means *specific and a little surprising* — not merely absent from the blocklist. Reach for a yardstick with cultural texture or a hook into this user's own world (the apps they build, their top project, their domain), and avoid the dry defaults that fit any token count — "X years of talking / typing / nonstop speech" is exactly that default and counts as stale, even though it sounds novel. Draft, then dodge the obvious: jot 3–4 candidate comparisons from *different* real-world domains, tag each for staleness (Wikipedia, distances to the moon, Olympic pools, War and Peace, "years of talking" all max out the meter — the ones every model reaches for first), bin the stalest, keep the sharpest, most specific one. **Ground it in a fact you actually know:** the conversion must rest on a stable, knowable constant (an audiobook ≈ 75,000 words; a flight ≈ a known number of hours) — never invent the figure a comparison needs (a video's view count, a film's runtime, box-office totals) just to make it land. If a yardstick only works with a number you're unsure of, it's the wrong yardstick — pick another. Pop-culture references are allowed but are seldom the right call for exactly this reason: they tend to be vivid only when propped up by a stat you'd be guessing at, and a fabricated number poisons the trust the accurate headline earned. If the stat you pick also powers a later slide, reframe that slide around a different angle or delete it — the deck never plays the same number twice.
- The **persona** (this drives the coral slide): invent one unique to this user — never pick from a stock list, and never reuse a name you'd give anyone else. Build it as a procedure: take their sharpest time-of-day trait from the hour histogram, fuse it with their sharpest behavioral trait from a second signal (top words, top projects, slash-command habits, `avgPromptChars`, streaks, please/thanks), and compress the pair into a "The ..." title. Rules:
  - Every trait in the name must be provable by a number on the slide or in its sub-copy.
  - The slide's chart shows hours, so the persona needs an hour-of-day angle; set `HOT_HOURS` to the hours that prove it. `HOT_HOURS` does double duty: its first hour also picks the persona crab's pose — pre-dawn (4–8) makes it sleepy, daytime (9–17) alert, evening/night (18–3) wired — so put the hour that matches the persona first. Non-hourly traits (weekend habits, politeness, prompt length) live in the second half of the name or the sub-copy.
  - Keep it a display headline: 2–5 words, title case, "The ..." form.
  - **Draft, then dodge the obvious — the step that kills the clone.** Before committing, jot 4 candidate names (names only, no rationale), each from a *different* pairing of signals, and tag each typicality H/M/L — H = likely to land in a stranger's deck (the hour-only "Night Owl", the "Perfectionist", the "Architect" are H, the modes every model reaches for first). Drop the H's; keep the lowest-typicality candidate that still proves out against the rules above.
- A `/clear` habit (memory-wipe jokes), a dominant slash command, a workflow obsession.
- The **head-to-head** (this drives the vs slide): invent the matchup with the most tension in this user's data — never default to one, never pick from a stock list. Procedure: list every same-unit pair the JSON offers, rank them by tension — a photo finish and an absurd blowout both land, a flat mid-ratio matchup doesn't — and take the most personal winner. `topWords` is usually the richest vein, because vocabulary tics are the most personal numbers in the JSON. Rules:
  - Fair fight: both sides share a unit (count vs count, hours vs hours), and both numbers come straight from the data.
  - Never replay a number an earlier slide already used, nor a word the top-words slide already shows.
  - **Draft, then dodge the obvious.** Jot 4 candidate matchups (one line each, no rationale) from different same-unit pairs and tag each typicality H/M/L — a please-vs-thanks or top-two-models bout is H. Drop the H's; keep the sharpest low-typicality matchup.
- A longest session left open absurdly long; a streak; a single enormous day.
- The **top words** (this drives the top-words slide): the user's most-typed words from `history.topWords` (already stopword-filtered, delivered as `[word, count]` pairs). Build the slide's bars from the top 4–5 (widest = the #1 word's count) and invent the copy from what those words reveal about what they built or how they think. Two hard rules so it doesn't fight its neighbours: never reuse a word the **head-to-head** or **persona** copy leans on (the deck never plays the same number, or word, twice), and if the list is thin or all generic filler, delete the slide rather than pad it.
- The **supporting cast** (this drives the delegation slide, only when `transcripts` is non-null): who this user actually leans on — a favourite subagent, a skill habit, or the installed-vs-used plugin gap (`plugins.installed` vs the plugin names actually appearing in `topSkills`/slash commands). Every line of this slide's copy — kicker, headline, sub, footnote — is invented from this user's delegation pattern; there is no stock framing. Two hard rules: the numbers are a recent-window subset, so the copy says "lately", never lifetime; and if the data is too thin to be funny (one tool call, no agents), delete the slide instead of padding it.

## Step 3 — Generate the page

**Chat output discipline.** While running Steps 1–4, do not narrate the template, your plan, or what you're about to do. Emit only a single short status line per step (e.g. "Analyzing your data…", "Writing your deck…"). The only wrap-up is the **fixed completion message** in Step 4 (and the share addendum in Step 5) — emit that verbatim and add no bespoke prose, no stats recap, no commentary of your own.

1. Copy `${CLAUDE_SKILL_DIR}/templates/template.html` to `./claude-unwrapped.html` in the current directory.
2. Replace **every** `{{PLACEHOLDER}}`. Search the file for `{{` when done — none may remain.
3. Get `USER_NAME` from `git config user.name` (first name only) or `$USER`. PERIOD_LABEL is the data date range, e.g. "January 13 — June 3, 2026".
4. Numeric slots used in `data-count` attributes (`HEADLINE_NUMBER`, `STREAK_DAYS`, `TOP_COMMAND_COUNT`) must be **raw integers**, no commas. `HEADLINE_UNIT` is the short line under the count-up naming what it counts — lowercase, ends with a period, the unit's name plus a short flourish invented for this user. `HOUR_DATA` is the 24-int JSON array from `history.hourHistogram`; `HOT_HOURS` is a JSON array of hour numbers.
5. Kicker and unit slots (`MODEL_KICKER`, `PROJECTS_KICKER`, `WORDS_KICKER`, `STREAK_KICKER`, `TOP_COMMAND_KICKER`, `CAST_KICKER`; `STREAK_UNIT`) are written fresh for this user like every other line. Kickers are short scene-setters, 2–5 words, in the deck's music-recap conceit — invent each one for this user. Unit lines complete the sentence the big number above them starts — lowercase, a few words, invented likewise.
6. Bar chart slots (`MODEL_BARS`, `PROJECT_BARS`, `WORD_BARS`, `CAST_BARS`): emit up to 5 rows, widest = 100%, others proportional. `WORD_BARS` rows are the top words with their counts; `CAST_BARS` rows are the top subagents and/or skills from `transcripts` — short names (strip a `plugin:` prefix when it reads better). Exact row markup (tab-indented three levels):

```html
<div class="bar-row"><span class="label">NAME</span><div class="bar-track"><div class="bar-fill" style="--w:NN%"></div></div><span class="val">COUNT</span></div>
```

Use `display` names for models and short basenames for projects. Format big values compactly (10.3B, 3,505).

7. If a whole section's data is missing (e.g. no `statsCache` → no token totals), delete that `<section>` entirely (including its `data-mood`) rather than faking numbers. The deck degrades gracefully — the crab walks across whatever slides remain and the finale fires on the last one. If you delete the persona section, still fill `HOUR_DATA` and `HOT_HOURS` — set both to `[]`.

## Voice guide — this is the part that matters

Write all copy in **Claude's first person**, addressing the user by name. The register: warm, wry, observant, self-aware about being an AI. Gentle roast, never mean. Concrete numbers beat adjectives. Patterns:

- Direct address with a hook: greet them by name, then pivot straight into the single most confronting habit their data shows.
- Self-aware AI humor: take one of their counts and narrate what it was like from your side, as the AI who lived through it — deadpan, specific.
- The parenthetical confession: a calm, dignified claim, immediately undercut by a parenthetical admitting the opposite — and citing where the evidence lives.
- Mock-grandiose comparison: convert a big number into an absurd real-world equivalent with the arithmetic actually done — something from *outside* Claude Code a person can picture: cultural ("X hours of Mr Beast videos"), physical ("X times up Everest"), temporal ("a paperback every Y days"). It must be **fresh and vary every generation** — never the tired defaults (Wikipedia, War and Peace, moon distances), which the Step 4 gate rejects, and never just another internal stat dressed up. **Use it sparingly — it's a highlight, not a tic.** It's required on the headline (the one genuinely unfathomable number) and allowed on **at most one other slide**, where a number truly needs grounding: **two yardsticks per deck maximum, from different domains.** Reserve it for numbers a person can't picture; human-scale ones (a 40-day streak, a thousand sessions) land better with the other patterns. Past two, the device curdles into a formula — the most generic thing a deck can do. And ground every comparison in a fact you actually know — never fabricate a number (views, runtimes, box office) to prop one up; if it needs a figure you're unsure of, choose a different yardstick.
- Footnotes are for the second, drier joke — a caveat or aside in small print.
- The outro leads with a one-line **verdict**: a bold, screenshot-worthy identity stamp, ideally a callback to their persona, peak hour, or top word, with a number welcome woven into the prose. Then a short forward-looking sign-off that proves you noticed their habits: their hour, their cadence, when they'll be back.

Never write generic filler ("What a year it's been!"). Every line must be earned by a specific number from this user's data and phrased in this user's vocabulary. The test for every sentence: if it would work in someone else's deck, it isn't done.

## Step 4 — Verify and open

1. Confirm no `{{` remains: `grep -c '{{' claude-unwrapped.html` must output 0.
2. Yardstick gate — **blocking, loop until it passes**:
	- *Present:* re-read the opening stat slide's sub copy. It **must** convert the headline number into a tangible real-world equivalent — an activity, object, distance, or duration a person can picture — not restate it as another internal metric (tokens, prompts, characters, sessions). If it doesn't, rewrite it so it does, then re-read. Its conversion must also rest on a fact you actually know — if you invented the number (a view count, a runtime) to make the comparison work, that's a fabrication; swap it for a yardstick built on a stable, knowable constant. Model-judged, but treat it as hard-blocking: do **not** `open` a deck whose headline has no real-world comparison, or one built on a number you guessed at.
	- *Fresh:* the yardstick must not be one of the worn-out defaults every model reaches for first. Run `grep -icE 'wikipedia|encyclopedia|war and peace|library of congress|to the moon|olympic.{0,12}pool|mount everest|times around the (earth|world)|football field|years of (talking|typing|speaking|speech)' claude-unwrapped.html`. Non-zero output = swap that yardstick for a fresher one and run the grep again. Repeat until it outputs 0. Substring over-matches are fine — when in doubt, rewrite anyway.
	- The `open` step below is forbidden until both checks pass. There is no exception.
3. Genericness gate — **blocking, loop until it passes**:
	- Run `grep -icE 'night owl|early bird|early riser|night shift|the perfectionist|the architect|the machine|the closer|the marathoner|on heavy rotation|now playing|top of the charts|chart.?topper|greatest hits' claude-unwrapped.html`. Non-zero output = a persona name or kicker fell into a stock mode; rewrite it from a sharper, less obvious signal and run the grep again. Repeat until it outputs 0. Substring over-matches are fine — when in doubt, rewrite anyway.
	- `open` stays forbidden until the grep outputs 0.
4. Syntax-check the inline JS: extract the `<script>` body to a temp file and run `node --check` on it (skip silently if node is unavailable).
5. Open it: `open claude-unwrapped.html` (macOS) or `xdg-open` (Linux).
6. Emit the completion message as **fixed text — not your own prose and not a stats recap**. Substitute the user's first name; change nothing else:
	> 🦀 {USER_NAME}, your Claude Unwrapped is ready — I've opened it in your browser. Give it a scroll.
	>
	> Help improve this plugin by visiting https://github.com/stuartshields/claude-unwrapped

	The GitHub line is always the **last** thing you say, on every run. On a share run, the Step 5 share lines slot in *between* the "ready" line and the GitHub line — never after it.

## Step 5 — Share file (only if asked)

If the user asks for a shareable link / share file (e.g. "/unwrapped:generate share", "make it shareable"), also write `./claude-unwrapped.share.json` — the same slide content as the HTML, as data. The share site validates strictly; follow this schema exactly (v2):

**Privacy review — runs before the file is written.**

1. Collect inline exclusions from the user's request first ("share without the projects slide", "share but hide coffee-app"). Both slides and individual items count.
2. Show what would go public: the slides the share will contain, plus every name its strings and bars mention — project names, command names, model names, fun-fact labels. Ask what to hold back, with any inline exclusions listed as already applied. In the same message, ask whether they want the share **listed on the share site's public homepage gallery** (alongside others who opted in) or kept **unlisted** (link-only) — default unlisted. Their answer sets `public`: `true` only on explicit opt-in, otherwise `false`. Uploading always yields a private link either way; `public` only controls the homepage listing, never who can open the link. One short message; don't paste the full copy. If the user says there's nothing to hide (or gives no new exclusions), write the file.
3. Apply exclusions:
	- **Excluded slide** → that section is `null` in the JSON. Any slide can be excluded except the cover and the outro; if the user asks to drop those, explain they always ship and offer to reword their copy instead. Copy-only slides (tokens, streak) have no items to hide — they are excluded whole or not at all.
	- **Hidden item** → remove its bar row, re-normalise the remaining bars (widest = 100), and rewrite every share string that mentioned it — headline, sub, footnote, outro copy — around the remaining data. If it was the slide's subject (e.g. the top project), reframe around the new #1. A chart left with zero bars means the whole slide is dropped. A name that appears only in copy (never in a bar) has no row to remove — just rewrite the strings.
4. Exclusions apply only to the share file. The local `claude-unwrapped.html` keeps everything.
5. Leak check — blocking, like the yardstick gate: run one grep per hidden name with the name substituted in, e.g. hiding coffee-app means `grep -ic 'coffee-app' claude-unwrapped.share.json`. Non-zero output = rewrite the offending string and run the grep again; repeat until every hidden name outputs 0. Substring over-matches are fine — when in doubt, rewrite anyway.

```json
{
	"version": 2,
	"userName": "…",
	"periodLabel": "…",
	"coverSub": "…",
	"public": false,
	"tokens":     { "total": 0, "kicker": "…", "sub": "…", "footnote": "…" },
	"model":      { "top": "…", "sub": "…", "bars": [ { "label": "…", "value": "…", "width": 100 } ] },
	"projects":   { "headline": "…", "sub": "…", "footnote": "…", "bars": [ { "label": "…", "value": "…", "width": 100 } ] },
	"topWords":   { "headline": "…", "sub": "…", "footnote": "…", "bars": [ { "label": "…", "value": "…", "width": 100 } ] },
	"persona":    { "name": "…", "sub": "…", "hourData": [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0], "hotHours": [22, 23] },
	"streak":     { "days": 0, "sub": "…", "footnote": "…" },
	"topCommand": { "command": "…", "count": 0, "headline": "…", "sub": "…", "footnote": "…" },
	"funFact":    { "kicker": "…", "sub": "…", "footnote": "…", "leftNum": "…", "leftLabel": "…", "rightNum": "…", "rightLabel": "…" },
	"outro":      { "verdict": "…", "headline": "…", "footnote": "…" }
}
```

Rules:

- String length caps: `userName` ≤60, `periodLabel` ≤100, kickers ≤120, headlines ≤120, subs ≤360, footnotes ≤220, bar `label` ≤60, bar `value` ≤16, `leftNum`/`rightNum` ≤16, `leftLabel`/`rightLabel` ≤80, outro `verdict` ≤120, `command` ≤80, persona `name` ≤80. Counts are capped at 1e12.
- Counts (`total`, `count`, `days`) are raw integers, no commas. Bar `value` is a display string ("10.3B", "3,505"). `width` is an integer 1–100, widest bar = 100.
- `public` is a boolean set from the homepage-listing prompt above: `true` only on explicit opt-in, otherwise `false`. It controls one thing — whether the share appears in the share site's public homepage gallery alongside others who opted in. Uploading always returns a private link regardless; `public` never changes who can view the link. Absent is treated as `false`, but always write it explicitly.
- 1–5 bars per chart; `hourData` is exactly the 24-int `history.hourHistogram`; `hotHours` are ints 0–23.
- Any slide you skipped in the HTML is `null` here — never invent data. No extra keys; the upload is rejected otherwise.
- **The share page is read by strangers, not the owner — never address the owner as "you"/"your".** Rewrite every string in third person using the owner's name or "they"/"their", keeping the narrator voice: a second-person address (`your <thing>`) becomes third person (`their <thing>` or `{owner}'s <thing>`); a line written *to* the owner ("You did X, N times") becomes one written *about* them ("{owner} did X, N times"). The share site's fixed headings already say "{{userName}}'s top model" etc. Don't just copy the HTML deck's strings — those are written to the owner.
- Bars are **data, not HTML** — the share site builds its own markup.
- Once the file is written and the leak check passes, slot the share lines into the Step 4 completion message — after the "ready" line, before the GitHub line — as **fixed text, not your own prose**. Use the URL exactly, then add the one line that matches `public`:
	> You've also generated your share file. Upload it at https://claudeunwrapped.live/ to get your link — it expires after 90 days.

	- `public: true` → add: "And you've made it public — the rest of the world is going to see how you use Claude. Nice work."
	- `public: false` → add: "It's unlisted, so no one but the people you share the link with (and me — Claude) will know your habits."

## Update one slide (instead of re-generating)

When the user wants to change just one slide of a deck they already made — a **fresh take** ("redo my persona slide", "make the head-to-head funnier") or a **directed edit** ("change the persona name to 'The X'", "fix the typo in the streak sub") — don't rebuild the deck. This mode needs `./claude-unwrapped.html` to exist; if it doesn't, run a normal generate (Steps 1–5) instead.

1. **Find the slide.** Read `./claude-unwrapped.html` and locate the target `<section class="slide">` by its heading and content. If you can't tell which slide they mean, ask — don't guess. If that slide isn't in the deck (it was dropped at generation for missing data), say so and offer a full regenerate rather than inventing it.
2. **Get its numbers only if you need them.** A pure copy edit (typo, reword) needs no data. For a fresh take, or any change that touches numbers, re-run the analyzer as in Step 1, **matching the existing deck's period** — its `PERIOD_LABEL` line, all-time unless that names a range. Only the target slide changes; every other slide stays byte-for-byte as it is.
3. **Rewrite only that slide:**
	- *Fresh take* → regenerate the slide's copy following the relevant Step 2 procedure (including the draft-and-dodge step for persona / head-to-head) and the Voice guide.
	- *Directed edit* → apply the specific change the user named; leave the rest of the slide intact.
	- Either way: keep Claude's voice and the user's name, leave the crab SVG / `data-mood` / script / every other slide untouched, and leave no `{{placeholder}}` behind.
4. **Stay consistent with the rest of the deck.** The other slides are fixed, so the updated copy must not replay a number, joke, or angle that already appears on another slide — the deck still never plays the same number twice.
5. **Verify — the same blocking gates as Step 4**, run over the whole file: `grep -c '{{'` = 0, the yardstick gate, and the genericness gate. Loop until each passes; reopening is forbidden until they do.
6. **Sync the share file.** If `./claude-unwrapped.share.json` exists, rewrite its matching section from the updated slide — but treat the *current* share file as the record of the user's earlier privacy choices: any item or whole slide the share omits relative to the deck was deliberately excluded, so keep it out and reframe around the remaining data (Step 5.3) — never reintroduce it on an update. Preserve the existing `public` value unchanged. Re-normalize any bars (widest = 100), apply the third-person rewrite (Step 5), and re-run the leak check against every name the share currently omits. A slide that's `null` in the share stays `null`.
7. **Reopen and report.** Re-open `claude-unwrapped.html` and emit the fixed completion message, naming the slide — no other prose:
	> 🦀 {USER_NAME}, I've refreshed your {slide} slide — reopening it.
	>
	> Help improve this plugin by visiting https://github.com/stuartshields/claude-unwrapped


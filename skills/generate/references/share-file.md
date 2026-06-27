# Share file (Step 5)

If the user asks for a shareable link / share file (e.g. "/unwrapped:generate share", "make it shareable"), also write `./claude-unwrapped.share.json` — the same slide content as the HTML, as data. The share site validates strictly; follow this schema exactly (v2):

**Privacy review — runs before the file is written.**

1. Collect inline exclusions from the user's request first ("share without the projects slide", "share but hide coffee-app"). Both slides and individual items count.
2. Show what would go public: the slides the share will contain, plus every name its strings and bars mention — project names, command names, model names, fun-fact labels. Ask what to hold back, with any inline exclusions listed as already applied. In the same message, ask whether they want the share **listed on the share site's public homepage gallery** (alongside others who opted in) or kept **unlisted** (link-only) — default unlisted. Their answer sets `public`: `true` only on explicit opt-in, otherwise `false`. **When `public` is true, also write a short, non-blank `title` (≤80 chars):** the homepage gallery card label, a punchy line that captures the deck (think headline, not sentence). The deck itself never renders it, and a public share with no title is rejected on upload. Uploading always yields a private link either way; `public` only controls the homepage listing, never who can open the link. One short message; don't paste the full copy. If the user says there's nothing to hide (or gives no new exclusions), write the file.
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
	"title": "…",
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

- String length caps: `userName` ≤60, `periodLabel` ≤100, kickers ≤120, headlines ≤120, subs ≤360, footnotes ≤220, bar `label` ≤60, bar `value` ≤16, `leftNum`/`rightNum` ≤16, `leftLabel`/`rightLabel` ≤80, outro `verdict` ≤120, `command` ≤80, persona `name` ≤80, gallery `title` ≤80. Counts are capped at 1e12.
- Counts (`total`, `count`, `days`) are raw integers, no commas. Bar `value` is a display string ("10.3B", "3,505"). `width` is an integer 1–100, widest bar = 100.
- `public` is a boolean set from the homepage-listing prompt above: `true` only on explicit opt-in, otherwise `false`. It controls one thing — whether the share appears in the share site's public homepage gallery alongside others who opted in. Uploading always returns a private link regardless; `public` never changes who can view the link. Absent is treated as `false`, but always write it explicitly.
- `title` is **required and non-blank** (≤80 chars) whenever `public` is `true`; omit it otherwise. It's the label on the homepage gallery card and is never rendered inside the deck. A public share with a missing or blank title is rejected on upload.
- 1–5 bars per chart; `hourData` is exactly the 24-int `history.hourHistogram`; `hotHours` are ints 0–23.
- Any slide you skipped in the HTML is `null` here — never invent data. No extra keys; the upload is rejected otherwise.
- **The share page is read by strangers, not the owner — never address the owner as "you"/"your".** Rewrite every string in third person using the owner's name or "they"/"their", keeping the narrator voice: a second-person address (`your <thing>`) becomes third person (`their <thing>` or `{owner}'s <thing>`); a line written *to* the owner ("You did X, N times") becomes one written *about* them ("{owner} did X, N times"). The share site's fixed headings already say "{{userName}}'s top model" etc. Don't just copy the HTML deck's strings — those are written to the owner.
- Bars are **data, not HTML** — the share site builds its own markup.
- Once the file is written and the leak check passes, slot the share lines into the Step 4 completion message — after the "ready" line, before the GitHub line — as **fixed text, not your own prose**. Use the URL exactly, then add the one line that matches `public`:
	> You've also generated your share file. Upload it at https://clawdunwrapped.live/ to get your link — it expires after 90 days.

	- `public: true` → add: "And you've made it public — the rest of the world is going to see how you use Claude. Nice work."
	- `public: false` → add: "It's unlisted, so no one but the people you share the link with (and me — Claude) will know your habits."

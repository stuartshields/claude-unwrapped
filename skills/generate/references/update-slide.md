# Update one slide (instead of re-generating)

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
	>
	> Like it? Support the project at https://ko-fi.com/claudeunwrapped


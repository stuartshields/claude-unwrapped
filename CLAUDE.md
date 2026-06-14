# claude-unwrapped

Claude Code plugin: `/unwrapped:generate` builds a Spotify-Wrapped-style HTML recap of the user's Claude Code usage from their local `~/.claude` data, narrated in Claude's first-person voice.

## Layout
- `.claude-plugin/plugin.json` — plugin manifest (name: `unwrapped`); `marketplace.json` — single-plugin marketplace (`source: "./"`) so the repo installs directly.
- `skills/generate/SKILL.md` — the skill: analyze → find the story → fill template → verify → open. The voice guide lives here; keep it.
- `skills/generate/scripts/analyze.py` — stdlib-only aggregator. Reads `stats-cache.json`, `history.jsonl`, `projects/*/*.jsonl`, `plugins/installed_plugins.json`. Honors `CLAUDE_CONFIG_DIR`, accepts a dir as argv[1] plus optional `--since`/`--until YYYY-MM-DD` (inclusive; ranged runs derive stats-cache totals from `dailyActivity`/`dailyModelTokens` and null the lifetime-only fields — output tokens, longest session, the `plugins` section). Emits one JSON to stdout with a `range` field echoing the filter. Every section nullable — never crash on missing files.
- `skills/generate/templates/template.html` — single-file deck with `{{PLACEHOLDER}}` slots. No build, no dependencies, vanilla CSS + JS only — keep it that way. The voice reference for generated copy is the voice guide in SKILL.md.
- Sharing: on request, the skill also writes `claude-unwrapped.share.json` (schema v2, spelled out in SKILL.md Step 5) for upload to the share Worker at `/Users/stuart/Personal/claude-unwrapped-cloudflare`. The Worker's `src/validate.ts` is the authoritative schema and its `src/template.html` is a vendored copy of the template — if you change template slots or the share schema, update SKILL.md *and* the Worker repo in the same change.

## Conventions
- Visual language: Anthropic brand — ivory `#FAF9F5`/`#F0EEE6`, coral `#D97757`, ink `#141413`, serif display type. The crab mascot is the native 🦀 emoji (`.crab` elements, sized via `font-size`).
- Slides are full-viewport scroll-snap `<section class="slide">` elements; reveals via IntersectionObserver adding `.in`; charts are CSS-only bars driven by `--w`/`--h` custom properties.
- Template placeholder contract: `data-count` slots take raw integers; `HOUR_DATA`/`HOT_HOURS` are JSON arrays; bar slots take `.bar-row` markup (exact snippet in SKILL.md). If you change template slots, update SKILL.md in the same commit.
- Test commands: `python3 skills/generate/scripts/test_analyze.py` (analyzer unit tests, stdlib unittest against a synthetic fixture dir), `python3 skills/generate/scripts/analyze.py ~/.claude | python3 -m json.tool > /dev/null` (analyzer smoke), HTML tag-balance + `node --check` on the extracted script (template).

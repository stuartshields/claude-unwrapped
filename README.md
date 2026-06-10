# Claude Unwrapped 🦀

Your Claude Code usage, Spotify-Wrapped style — a single scroll-snap HTML page narrated by Claude itself, starring the crab. Built entirely from the data already sitting in your `~/.claude` directory. Nothing leaves your machine.

## What you get

Ten full-screen slides in the Anthropic palette: an opening headline stat picked to alarm you — usually your token total, counted up before your eyes — sessions, your top model on heavy rotation, top projects, a coding personality invented just for you from your hours, habits, and vocabulary, your longest streak, your most played slash command, a head-to-head fun fact invented from your data (maybe "please" vs "thanks", maybe your two favourite words in a photo finish), and an outro that knows exactly what time you'll be back tomorrow.

The copy is written fresh each time, in Claude's voice, from *your* numbers — not a fill-in-the-blanks mad lib.

## Install

**No marketplace needed.** Pick whichever suits you:

**Option 1 — skills directory (persistent, simplest).** Clone or symlink the repo into your skills directory and it auto-loads on next launch — no install command at all:

```bash
git clone <repo-url> ~/.claude/skills/unwrapped
# or, from a clone elsewhere:
ln -s /path/to/claude-unwrapped ~/.claude/skills/unwrapped
```

Run it with `/unwrapped:generate`.

**Option 2 — session flag (try it once).** Point Claude Code at the clone for a single session:

```bash
claude --plugin-dir /path/to/claude-unwrapped
```

**Option 3 — marketplace (classic).** The repo doubles as its own single-plugin marketplace:

```
/plugin marketplace add /path/to/claude-unwrapped   # or <owner>/claude-unwrapped from GitHub
/plugin install unwrapped@claude-unwrapped
```

## Run

```
/unwrapped:generate
```

Claude runs the bundled analyzer (stdlib Python, no dependencies) over your `~/.claude` — `stats-cache.json`, `history.jsonl`, and any retained transcripts — picks the funniest patterns it finds, fills the template, and opens `claude-unwrapped.html` in your browser.

Point it at a non-default config dir if you use one:

```
/unwrapped:generate ~/.claude-work
```

### A recap for any period

All-time is the default. Ask for a period in plain language and Claude passes the matching dates to the analyzer:

```
/unwrapped:generate this month
/unwrapped:generate Q1 2026
/unwrapped:generate since March
/unwrapped:generate ~/.claude-work for last week
```

Two things to know about ranged recaps:

- A few stats only exist as lifetime totals (output tokens, longest session). Those slides are skipped or reframed instead of showing all-time numbers.
- Tool-usage flavor comes from locally retained transcripts, which usually cover only the last few weeks. Older ranges get a recap without it.

Want raw numbers instead of slides? Run the analyzer yourself — `--since` and `--until` take `YYYY-MM-DD`, are inclusive, and each works alone:

```bash
python3 skills/generate/scripts/analyze.py --since 2026-03-01 --until 2026-03-31
python3 skills/generate/scripts/analyze.py --since 2026-06-01   # June 1 → today
```

## Privacy

Everything is local: the analyzer reads your `~/.claude` directory, the output is a static HTML file in your current directory, and no network requests are made by the script or the page.

## Requirements

- `python3` on PATH (stdlib only)
- Claude Code with plugin support

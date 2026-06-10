# Claude Unwrapped 🦀

Your Claude Code usage, Spotify-Wrapped style — a single scroll-snap HTML page narrated by Claude itself, starring the crab. Built entirely from the data already sitting in your `~/.claude` directory. Nothing leaves your machine.

## What you get

Ten full-screen slides in the Anthropic palette: total tokens (with an animated count-up of a number that will alarm you), sessions, your top model on heavy rotation, top projects, a coding personality derived from your hour-of-day histogram, your longest streak, your most played slash command, a head-to-head fun fact ("please" vs "thanks"), and an outro that knows exactly what time you'll be back tomorrow.

The copy is written fresh each time, in Claude's voice, from *your* numbers — not a fill-in-the-blanks mad lib.

## Install

**No marketplace needed.** Pick whichever suits you:

**Option 1 — skills directory (persistent, simplest).** Clone or symlink the repo into your skills directory and it auto-loads on next launch — no install command at all:

```bash
git clone <repo-url> ~/.claude/skills/unwrapped
# or, from a clone elsewhere:
ln -s /path/to/ai-code-unwrapped ~/.claude/skills/unwrapped
```

Run it with `/unwrapped:generate`.

**Option 2 — session flag (try it once).** Point Claude Code at the clone for a single session:

```bash
claude --plugin-dir /path/to/ai-code-unwrapped
```

**Option 3 — marketplace (classic).** The repo doubles as its own single-plugin marketplace:

```
/plugin marketplace add /path/to/ai-code-unwrapped   # or <owner>/ai-code-unwrapped from GitHub
/plugin install unwrapped@ai-code-unwrapped
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

## Privacy

Everything is local: the analyzer reads your `~/.claude` directory, the output is a static HTML file in your current directory, and no network requests are made by the script or the page.

## Requirements

- `python3` on PATH (stdlib only)
- Claude Code with plugin support

#!/usr/bin/env python3
"""Aggregate Claude Code usage stats from the user's ~/.claude directory.

Reads stats-cache.json (sessions, messages, tokens, models), history.jsonl
(every prompt typed), and projects/*/*.jsonl transcripts (tool calls).
Emits a single JSON object on stdout. Stdlib only. Every section is
optional — missing files produce nulls, never a crash.
"""
import argparse
import collections
import datetime
import glob
import json
import os
import re
import sys


def parse_args():
	p = argparse.ArgumentParser(description=__doc__)
	p.add_argument("claude_dir", nargs="?",
		default=os.environ.get("CLAUDE_CONFIG_DIR", "~/.claude"))
	p.add_argument("--since", type=datetime.date.fromisoformat,
		metavar="YYYY-MM-DD", help="only count activity on or after this date")
	p.add_argument("--until", type=datetime.date.fromisoformat,
		metavar="YYYY-MM-DD", help="only count activity on or before this date")
	return p.parse_args()


ARGS = parse_args()
CLAUDE_DIR = os.path.expanduser(ARGS.claude_dir)
SINCE, UNTIL = ARGS.since, ARGS.until
RANGED = SINCE is not None or UNTIL is not None


def in_range(date):
	return (SINCE is None or date >= SINCE) and (UNTIL is None or date <= UNTIL)

STOPWORDS = set("""
the a an to and of in is it for on with that this you i be as at if or my we
from are was can do does not no yes but so just its it's into your me they
them there their then than what when how why which will would should could
have has had about all out up down use using make made get got when where
who whom these those any some more most other another such only own same too
very don't dont doesn't isn't won't can't need needs want wants like also
now new one two way each after before been being because over under again
let lets let's please thanks thank still well back able
""".split())

MODEL_FAMILY = re.compile(r"^claude-([a-z]+)-(\d+)(?:[.-](\d+))?")


def model_display_name(model_id):
	m = MODEL_FAMILY.match(model_id)
	if not m:
		return model_id
	family = m.group(1).capitalize()
	version = m.group(2) + ("." + m.group(3) if m.group(3) else "")
	return f"{family} {version}"


def parse_day(s):
	try:
		return datetime.date.fromisoformat(s or "")
	except ValueError:
		return None


def day_in_range(entry):
	day = parse_day(entry.get("date"))
	return day is not None and in_range(day)


def load_stats_cache():
	path = os.path.join(CLAUDE_DIR, "stats-cache.json")
	try:
		with open(path) as f:
			d = json.load(f)
	except (OSError, json.JSONDecodeError):
		return None

	daily = d.get("dailyActivity") or []
	if RANGED:
		daily = [x for x in daily if day_in_range(x)]
	busiest = max(daily, key=lambda x: x.get("messageCount", 0), default=None)

	models = {}
	total_tokens = 0
	if RANGED:
		# modelUsage and longestSession are lifetime aggregates the cache
		# never breaks down by day; only dailyModelTokens (total tokens per
		# model per date, no output split) can honor the range.
		for day in (d.get("dailyModelTokens") or []):
			if not day_in_range(day):
				continue
			for model_id, tokens in (day.get("tokensByModel") or {}).items():
				m = models.setdefault(model_id, {
					"display": model_display_name(model_id),
					"totalTokens": 0,
					"outputTokens": None,
				})
				m["totalTokens"] += tokens
				total_tokens += tokens
		total_output = None
		total_sessions = sum(x.get("sessionCount", 0) for x in daily)
		total_messages = sum(x.get("messageCount", 0) for x in daily)
		longest = {}
	else:
		total_output = 0
		for model_id, usage in (d.get("modelUsage") or {}).items():
			tokens = sum(usage.get(k, 0) for k in (
				"inputTokens", "outputTokens",
				"cacheReadInputTokens", "cacheCreationInputTokens",
			))
			models[model_id] = {
				"display": model_display_name(model_id),
				"totalTokens": tokens,
				"outputTokens": usage.get("outputTokens", 0),
			}
			total_tokens += tokens
			total_output += usage.get("outputTokens", 0)
		total_sessions = d.get("totalSessions")
		total_messages = d.get("totalMessages")
		longest = d.get("longestSession") or {}

	return {
		"lastComputedDate": d.get("lastComputedDate"),
		"firstSessionDate": d.get("firstSessionDate"),
		"totalSessions": total_sessions,
		"totalMessages": total_messages,
		"totalToolCalls": sum(x.get("toolCallCount", 0) for x in daily),
		"busiestDay": busiest,
		"totalTokens": total_tokens,
		"totalOutputTokens": total_output,
		"models": dict(sorted(models.items(), key=lambda kv: -kv[1]["totalTokens"])),
		"longestSession": {
			"messageCount": longest.get("messageCount"),
			"hours": round(longest.get("duration", 0) / 3_600_000, 1),
		} if longest else None,
	}


def longest_streak(dates):
	run = best = 1 if dates else 0
	ordered = sorted(dates)
	for prev, cur in zip(ordered, ordered[1:]):
		run = run + 1 if (cur - prev).days == 1 else 1
		best = max(best, run)
	return best


def analyze_history():
	path = os.path.join(CLAUDE_DIR, "history.jsonl")
	if not os.path.exists(path):
		return None

	projects = collections.Counter()
	hours = collections.Counter()
	weekdays = collections.Counter()
	slash = collections.Counter()
	words = collections.Counter()
	sessions = set()
	dates = set()
	lengths = []
	please = thanks = 0
	first_ts = last_ts = None

	with open(path, errors="replace") as f:
		for line in f:
			try:
				e = json.loads(line)
			except json.JSONDecodeError:
				continue
			ts = e.get("timestamp")
			dt = datetime.datetime.fromtimestamp(ts / 1000) if ts else None
			if RANGED and (dt is None or not in_range(dt.date())):
				continue
			if dt:
				hours[dt.hour] += 1
				weekdays[dt.strftime("%A")] += 1
				dates.add(dt.date())
				first_ts = ts if first_ts is None else min(first_ts, ts)
				last_ts = ts if last_ts is None else max(last_ts, ts)
			if e.get("project"):
				projects[os.path.basename(e["project"])] += 1
			if e.get("sessionId"):
				sessions.add(e["sessionId"])
			display = (e.get("display") or "").strip()
			if not display:
				continue
			lengths.append(len(display))
			if display.startswith("/"):
				slash[display.split()[0].lower()] += 1
			low = display.lower()
			please += len(re.findall(r"\bplease\b", low))
			thanks += len(re.findall(r"\bthanks?\b|\bthank you\b", low))
			for w in re.findall(r"[a-z']{3,}", low):
				if w not in STOPWORDS:
					words[w] += 1

	def iso(ts):
		return datetime.datetime.fromtimestamp(ts / 1000).date().isoformat() if ts else None

	return {
		"promptCount": len(lengths),
		"sessionIds": len(sessions),
		"firstPromptDate": iso(first_ts),
		"lastPromptDate": iso(last_ts),
		"activeDays": len(dates),
		"longestStreakDays": longest_streak(dates),
		"avgPromptChars": round(sum(lengths) / len(lengths)) if lengths else 0,
		"maxPromptChars": max(lengths, default=0),
		"hourHistogram": [hours.get(h, 0) for h in range(24)],
		"weekdays": dict(weekdays.most_common()),
		"topProjects": projects.most_common(8),
		"topSlashCommands": slash.most_common(10),
		"topWords": words.most_common(25),
		"saidPlease": please,
		"saidThanks": thanks,
	}


def iso_local_date(ts):
	try:
		dt = datetime.datetime.fromisoformat((ts or "").replace("Z", "+00:00"))
	except ValueError:
		return None
	return dt.astimezone().date()


def analyze_transcripts():
	pattern = os.path.join(CLAUDE_DIR, "projects", "*", "*.jsonl")
	tools = collections.Counter()
	agents = collections.Counter()
	for fp in glob.glob(pattern):
		try:
			with open(fp, errors="replace") as f:
				for line in f:
					if '"tool_use"' not in line:
						continue
					try:
						e = json.loads(line)
					except json.JSONDecodeError:
						continue
					if RANGED:
						day = iso_local_date(e.get("timestamp"))
						if day is None or not in_range(day):
							continue
					for c in ((e.get("message") or {}).get("content") or []):
						if isinstance(c, dict) and c.get("type") == "tool_use":
							tools[c.get("name", "?")] += 1
							if c.get("name") in ("Task", "Agent"):
								agents[(c.get("input") or {}).get("subagent_type", "general")] += 1
		except OSError:
			continue
	if not tools:
		return None
	return {
		"note": "from locally retained transcripts only; likely a subset of all-time usage",
		"topTools": tools.most_common(12),
		"topAgents": agents.most_common(8),
	}


def main():
	out = {
		"generatedAt": datetime.datetime.now().isoformat(timespec="seconds"),
		"claudeDir": CLAUDE_DIR,
		"range": {
			"since": SINCE.isoformat() if SINCE else None,
			"until": UNTIL.isoformat() if UNTIL else None,
		} if RANGED else None,
		"statsCache": load_stats_cache(),
		"history": analyze_history(),
		"transcripts": analyze_transcripts(),
	}
	if out["statsCache"] is None and out["history"] is None:
		print(json.dumps({"error": f"No usage data found in {CLAUDE_DIR} "
			"(expected stats-cache.json and/or history.jsonl)"}))
		sys.exit(1)
	print(json.dumps(out, indent=1))


if __name__ == "__main__":
	main()

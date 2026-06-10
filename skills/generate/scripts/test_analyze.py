#!/usr/bin/env python3
"""Tests for analyze.py date-range filtering. Stdlib only.

Run: python3 -m unittest skills.generate.scripts.test_analyze
  or: python3 skills/generate/scripts/test_analyze.py
"""
import datetime
import json
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "analyze.py")

JAN_DATE = datetime.date(2026, 1, 15)
MAR_DATE = datetime.date(2026, 3, 15)


def epoch_ms(date, hour):
	"""Epoch milliseconds for a local date+hour, matching history.jsonl."""
	dt = datetime.datetime(date.year, date.month, date.day, hour)
	return int(dt.timestamp() * 1000)


def history_entry(date, hour, display, session):
	return {
		"display": display,
		"timestamp": epoch_ms(date, hour),
		"project": "/Users/x/proj",
		"sessionId": session,
		"pastedContents": {},
	}


OPUS = "claude-opus-4-5-20251101"
HAIKU = "claude-haiku-4-5-20251001"

STATS_CACHE = {
	"lastComputedDate": "2026-04-09",
	"firstSessionDate": "2026-01-13T02:00:00.000Z",
	"totalSessions": 10,
	"totalMessages": 1000,
	"dailyActivity": [
		{"date": "2026-01-15", "messageCount": 100, "sessionCount": 2, "toolCallCount": 40},
		{"date": "2026-03-15", "messageCount": 200, "sessionCount": 3, "toolCallCount": 50},
		{"date": "2026-03-16", "messageCount": 50, "sessionCount": 1, "toolCallCount": 10},
	],
	"dailyModelTokens": [
		{"date": "2026-01-15", "tokensByModel": {OPUS: 1000}},
		{"date": "2026-03-15", "tokensByModel": {OPUS: 2000, HAIKU: 500}},
	],
	"modelUsage": {
		OPUS: {"inputTokens": 10, "outputTokens": 20,
			"cacheReadInputTokens": 30, "cacheCreationInputTokens": 40},
	},
	"longestSession": {"messageCount": 500, "duration": 7200000},
}


def build_fixture(root):
	"""Synthetic CLAUDE dir: 2 prompts in January, 3 in March."""
	entries = [
		history_entry(JAN_DATE, 9, "january prompt one", "s1"),
		history_entry(JAN_DATE, 10, "january prompt two", "s1"),
		history_entry(MAR_DATE, 9, "march prompt one", "s2"),
		history_entry(MAR_DATE, 10, "march prompt two", "s2"),
		history_entry(MAR_DATE, 11, "march prompt three", "s3"),
	]
	with open(os.path.join(root, "history.jsonl"), "w") as f:
		for e in entries:
			f.write(json.dumps(e) + "\n")
	with open(os.path.join(root, "stats-cache.json"), "w") as f:
		json.dump(STATS_CACHE, f)
	proj = os.path.join(root, "projects", "-Users-x-proj")
	os.makedirs(proj)
	lines = [
		transcript_line(JAN_DATE, "Bash"),
		transcript_line(JAN_DATE, "Bash"),
		transcript_line(JAN_DATE, "Skill", {"skill": "superpowers:brainstorming"}),
		transcript_line(MAR_DATE, "Read"),
		transcript_line(MAR_DATE, "Task", {"subagent_type": "code-reviewer"}),
		transcript_line(MAR_DATE, "Skill", {"skill": "plan-cycle"}),
	]
	with open(os.path.join(proj, "t.jsonl"), "w") as f:
		for line in lines:
			f.write(json.dumps(line) + "\n")
	plug = os.path.join(root, "plugins")
	os.makedirs(plug)
	with open(os.path.join(plug, "installed_plugins.json"), "w") as f:
		json.dump({"version": 2, "plugins": {
			"superpowers@obra": [{"scope": "user"}],
			"frontend-design@claude-plugins-official": [{"scope": "project"}],
		}}, f)


def transcript_line(date, tool, tool_input=None):
	return {
		"type": "assistant",
		"timestamp": f"{date.isoformat()}T12:00:00.000Z",
		"message": {"content": [
			{"type": "tool_use", "name": tool, "input": tool_input or {}},
		]},
	}


def run_analyze(*args):
	out = subprocess.run(
		[sys.executable, SCRIPT, *args],
		capture_output=True, text=True,
	)
	return out.returncode, json.loads(out.stdout) if out.stdout else None


class TestDateRange(unittest.TestCase):
	def setUp(self):
		self.tmp = tempfile.TemporaryDirectory()
		build_fixture(self.tmp.name)

	def tearDown(self):
		self.tmp.cleanup()

	def test_history_filtered_to_range(self):
		code, out = run_analyze(
			self.tmp.name, "--since", "2026-03-01", "--until", "2026-03-31")
		self.assertEqual(code, 0)
		h = out["history"]
		self.assertEqual(h["promptCount"], 3)
		self.assertEqual(h["activeDays"], 1)
		self.assertEqual(h["sessionIds"], 2)
		self.assertEqual(h["firstPromptDate"], "2026-03-15")
		self.assertEqual(h["lastPromptDate"], "2026-03-15")

	def test_stats_cache_derived_from_daily_fields_when_ranged(self):
		code, out = run_analyze(
			self.tmp.name, "--since", "2026-03-01", "--until", "2026-03-31")
		self.assertEqual(code, 0)
		sc = out["statsCache"]
		self.assertEqual(sc["totalSessions"], 4)
		self.assertEqual(sc["totalMessages"], 250)
		self.assertEqual(sc["totalToolCalls"], 60)
		self.assertEqual(sc["busiestDay"]["date"], "2026-03-15")
		self.assertEqual(sc["models"][OPUS]["totalTokens"], 2000)
		self.assertEqual(sc["models"][HAIKU]["totalTokens"], 500)
		self.assertEqual(sc["totalTokens"], 2500)
		self.assertIsNone(sc["totalOutputTokens"])
		self.assertIsNone(sc["longestSession"])

	def test_transcript_tool_calls_filtered_to_range(self):
		code, out = run_analyze(
			self.tmp.name, "--since", "2026-03-01", "--until", "2026-03-31")
		self.assertEqual(code, 0)
		t = out["transcripts"]
		self.assertEqual(dict(t["topTools"]), {"Read": 1, "Task": 1, "Skill": 1})
		self.assertEqual(dict(t["topAgents"]), {"code-reviewer": 1})
		self.assertEqual(dict(t["topSkills"]), {"plan-cycle": 1})

	def test_output_echoes_active_range(self):
		code, out = run_analyze(
			self.tmp.name, "--since", "2026-03-01", "--until", "2026-03-31")
		self.assertEqual(code, 0)
		self.assertEqual(out["range"], {"since": "2026-03-01", "until": "2026-03-31"})

	def test_no_flags_keeps_all_time_behavior(self):
		code, out = run_analyze(self.tmp.name)
		self.assertEqual(code, 0)
		self.assertIsNone(out["range"])
		self.assertEqual(out["history"]["promptCount"], 5)
		self.assertEqual(out["history"]["activeDays"], 2)
		sc = out["statsCache"]
		self.assertEqual(sc["totalSessions"], 10)
		self.assertEqual(sc["totalMessages"], 1000)
		self.assertEqual(sc["totalTokens"], 100)
		self.assertEqual(sc["totalOutputTokens"], 20)
		self.assertEqual(sc["longestSession"], {"messageCount": 500, "hours": 2.0})
		self.assertEqual(
			dict(out["transcripts"]["topTools"]),
			{"Bash": 2, "Read": 1, "Task": 1, "Skill": 2})
		self.assertEqual(
			dict(out["transcripts"]["topSkills"]),
			{"superpowers:brainstorming": 1, "plan-cycle": 1})
		self.assertEqual(out["plugins"],
			{"installed": 2, "names": ["frontend-design", "superpowers"]})

	def test_plugins_null_when_ranged(self):
		code, out = run_analyze(
			self.tmp.name, "--since", "2026-03-01", "--until", "2026-03-31")
		self.assertEqual(code, 0)
		self.assertIsNone(out["plugins"])

	def test_plugins_null_when_inventory_missing(self):
		with tempfile.TemporaryDirectory() as root:
			with open(os.path.join(root, "history.jsonl"), "w") as f:
				f.write(json.dumps(history_entry(JAN_DATE, 9, "hi", "s1")) + "\n")
			code, out = run_analyze(root)
			self.assertEqual(code, 0)
			self.assertIsNone(out["plugins"])


if __name__ == "__main__":
	unittest.main()

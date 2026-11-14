#!/usr/bin/env python3
"""Tests for scripts/check_index.py."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_index", ROOT / "scripts" / "check_index.py")
assert spec and spec.loader
idx = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = idx
spec.loader.exec_module(idx)


class CheckIndexTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "experiments" / "alpha").mkdir(parents=True)
        (self.root / "experiments" / "beta").mkdir(parents=True)
        (self.root / "notes" / "assets").mkdir(parents=True)
        (self.root / "notes" / "gate.md").write_text("# gate\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _records(self, text: str) -> list[str]:
        index = self.root / "experiments" / "README.md"
        index.write_text(text, encoding="utf-8")
        return idx.check(idx.record_folders(self.root), index, idx.RECORD_STATUSES)

    def test_all_indexed_with_status_passes(self) -> None:
        text = "| [Alpha](alpha/) | q | `complete` |\n| [Beta](./beta) | q | `pilot` |\n"
        self.assertEqual(self._records(text), [])

    def test_missing_entry_fails(self) -> None:
        problems = self._records("| [Alpha](alpha/) | q | `complete` |\n")
        self.assertEqual(len(problems), 1)
        self.assertIn("no entry links beta", problems[0])

    def test_missing_status_fails(self) -> None:
        text = "| [Alpha](alpha/) | q | complete |\n| [Beta](beta/) | q | `pilot` |\n"
        problems = self._records(text)
        self.assertEqual(len(problems), 1)
        self.assertIn("alpha has no status", problems[0])

    def test_unknown_status_fails(self) -> None:
        text = "| [Alpha](alpha/) | q | `amazing` |\n| [Beta](beta/) | q | `pilot` |\n"
        self.assertEqual(len(self._records(text)), 1)

    def test_link_with_file_and_anchor_counts_for_folder_only_when_exact(self) -> None:
        text = "| [Alpha](alpha/README.md) | q | `complete` |\n| [Beta](beta/#results) | q | `pilot` |\n"
        problems = self._records(text)
        self.assertEqual(problems, [f"{self.root / 'experiments' / 'README.md'}: no entry links alpha"])

    def test_notes_ignore_supporting_folders(self) -> None:
        index = self.root / "notes" / "README.md"
        index.write_text("- [Gate](gate.md): `idea`\n", encoding="utf-8")
        self.assertEqual(idx.note_files(self.root), ["gate.md"])
        self.assertEqual(idx.check(idx.note_files(self.root), index, idx.NOTE_STATUSES), [])

    def test_repository_indexes_pass(self) -> None:
        problems = idx.check(idx.record_folders(), ROOT / "experiments" / "README.md", idx.RECORD_STATUSES)
        problems += idx.check(idx.note_files(), ROOT / "notes" / "README.md", idx.NOTE_STATUSES)
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()

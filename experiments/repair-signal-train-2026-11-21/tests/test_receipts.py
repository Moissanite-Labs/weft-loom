import contextlib
import io
import json
import os
import tempfile
import unittest

import _setup  # noqa: F401
import receipts as R


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "r.jsonl")
        for i in range(4):
            R.append(self.path, {"kind": "eval", "i": i, "name": "n%d" % i, "rate_num": i, "rate_den": 4})

    def tearDown(self):
        self.tmp.cleanup()

    def lines(self):
        with open(self.path, "r", encoding="utf-8") as fh:
            return fh.read().split("\n")[:-1]

    def write(self, lines):
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")

    def test_append_and_bodies_check_the_head_they_are_given(self):
        count, head = R.verify(self.path)
        R.bodies(self.path, head)
        with self.assertRaises(R.ReceiptError):
            R.bodies(self.path, "0" * 64)
        with self.assertRaises(R.ReceiptError):
            R.append(self.path, {"kind": "x"}, "0" * 64)
        self.assertEqual(R.verify(self.path)[0], count)               # the refused append wrote nothing
        new_head = R.append(self.path, {"kind": "x"}, head)
        self.assertEqual(R.verify(self.path), (count + 1, new_head))

    def test_chain_verifies_and_head_matches_append(self):
        n, head = R.verify(self.path)
        self.assertEqual(n, 4)
        self.assertEqual(R.append(self.path, {"x": 1}), R.verify(self.path)[1])
        self.assertNotEqual(head, R.verify(self.path)[1])

    def test_edit_in_the_middle_fails(self):
        ls = self.lines()
        ls[1] = ls[1].replace('"i":1', '"i":9')
        self.write(ls)
        with self.assertRaises(R.ReceiptError):
            R.verify(self.path)

    def test_edit_of_the_last_line_fails_its_own_hash(self):
        ls = self.lines()
        ls[-1] = ls[-1].replace('"i":3', '"i":9')
        self.write(ls)
        with self.assertRaises(R.ReceiptError) as cm:
            R.verify(self.path)
        self.assertIn("own hash", str(cm.exception))

    def test_edit_with_recomputed_self_hash_is_caught_by_the_next_line(self):
        ls = self.lines()
        rec = json.loads(ls[1])
        rec["body"]["i"] = 9
        rec["self"] = R._self_hash(rec["seq"], rec["prev"], rec["body"])
        ls[1] = R._canon(rec)
        self.write(ls)
        with self.assertRaises(R.ReceiptError) as cm:
            R.verify(self.path)
        self.assertIn("does not chain", str(cm.exception))

    def test_last_line_rewritten_with_new_self_needs_the_head(self):
        ls = self.lines()
        rec = json.loads(ls[-1])
        rec["body"]["i"] = 9
        rec["self"] = R._self_hash(rec["seq"], rec["prev"], rec["body"])
        old_head = R.verify(self.path)[1]
        ls[-1] = R._canon(rec)
        self.write(ls)
        R.verify(self.path)                       # the file alone cannot see this
        with self.assertRaises(R.ReceiptError):
            R.verify(self.path, expect_head=old_head)

    def test_wrong_sequence_number_fails_even_with_a_recomputed_hash(self):
        ls = self.lines()
        rec = json.loads(ls[-1])
        rec["seq"] = 7
        rec["self"] = R._self_hash(rec["seq"], rec["prev"], rec["body"])
        ls[-1] = R._canon(rec)
        self.write(ls)
        with self.assertRaises(R.ReceiptError) as cm:
            R.verify(self.path)
        self.assertIn("seq", str(cm.exception))

    def test_deleted_and_reordered_lines_fail(self):
        ls = self.lines()
        self.write(ls[:1] + ls[2:])
        with self.assertRaises(R.ReceiptError):
            R.verify(self.path)
        self.write([ls[1], ls[0]] + ls[2:])
        with self.assertRaises(R.ReceiptError):
            R.verify(self.path)

    def test_missing_newline_fails(self):
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write("{")
        with self.assertRaises(R.ReceiptError):
            R.verify(self.path)

    def test_floats_and_other_types_are_refused_on_append(self):
        for bad in ({"a": 0.5}, {"a": True}, {"a": None}, {"a": [1, 2.0]}, {"a": {"b": 1.5}}, {1: "x"}, {"a": (1, 2)}):
            with self.assertRaises(R.ReceiptError, msg=str(bad)):
                R.append(self.path, bad)
        self.assertEqual(R.verify(self.path)[0], 4)

    def test_a_float_in_the_file_fails_verification(self):
        ls = self.lines()
        ls[0] = ls[0].replace('"i":0', '"i":0.0')
        self.write(ls)
        with self.assertRaises(R.ReceiptError):
            R.verify(self.path)

    def test_cli(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(R.main(["receipts.py", "verify", self.path]), 0)
            self.assertEqual(R.main(["receipts.py", "verify", self.path, "--head", "0" * 64]), 1)
            self.assertEqual(R.main(["receipts.py"]), 2)

    def test_big_integers_are_fine(self):
        R.append(self.path, {"p_den": 2 ** 200})
        self.assertEqual(R.bodies(self.path)[-1]["p_den"], 2 ** 200)


if __name__ == "__main__":
    unittest.main()

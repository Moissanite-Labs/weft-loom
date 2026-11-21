import contextlib
import io
import re
import tempfile
import unittest

import _setup  # noqa: F401
import dryrun


class DryRunTests(unittest.TestCase):
    def test_dry_run_passes_every_check(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), tempfile.TemporaryDirectory() as tmp:
            rc = dryrun.run(tmp, None)
        out = buf.getvalue()
        self.assertEqual(rc, 0, out)
        self.assertNotIn("FAIL", out)
        for needle in ("latch refuses a second touch", "an edited receipt fails verification",
                       "a changed rsig hash refuses to run", "unapproved run id", "identical to the baseline",
                       "different compute cap", "not in the receipt chain", "not registered",
                       "second set was touched once and support holds", "never touched"):
            self.assertIn(needle, out)
        self.assertRegex(out, r"\d+ checks, 0 failed")

    def test_output_has_no_paths(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), tempfile.TemporaryDirectory() as tmp:
            dryrun.run(tmp, None)
        self.assertNotIn(tmp, buf.getvalue())
        self.assertIsNone(re.search(r"/(Users|home|private|tmp|var)/", buf.getvalue()))


class HygieneTests(unittest.TestCase):
    def test_no_bare_assert_and_no_float_literals_in_checking_modules(self):
        import os
        for name in os.listdir(_setup.LOOP):
            if name.endswith(".py"):
                with open(os.path.join(_setup.LOOP, name), encoding="utf-8") as fh:
                    for i, ln in enumerate(fh, 1):
                        self.assertFalse(ln.lstrip().startswith("assert "), "%s:%d" % (name, i))
        for name in ("receipts.py", "ratchet.py", "evaluate.py", "latch.py", "episodes.py", "codec.py", "driver.py",
                     "cost.py"):
            with open(os.path.join(_setup.LOOP, name), encoding="utf-8") as fh:
                src = fh.read()
            self.assertIsNone(re.search(r"\bfloat\(", src), name)
            self.assertIsNone(re.search(r"[^\w\"'.][0-9]+\.[0-9]+", re.sub(r'"[^"\n]*"|#.*', "", src)), name)


if __name__ == "__main__":
    unittest.main()

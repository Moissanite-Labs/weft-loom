import importlib.util
import io
import os
import contextlib
import unittest

import _setup  # noqa: F401

HAVE_LIBRARY = bool(importlib.util.find_spec("tinker")) and bool(importlib.util.find_spec("tml_renderers"))


@unittest.skipUnless(HAVE_LIBRARY, "needs the installed service library and tml_renderers")
class ApiCheckTests(unittest.TestCase):
    def test_the_backend_conforms_to_the_installed_library(self):
        path = os.path.join(_setup.LOOP, "checks", "tinker_api_check.py")
        spec = importlib.util.spec_from_file_location("tinker_api_check", path)
        mod = importlib.util.module_from_spec(spec)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            spec.loader.exec_module(mod)
            code = mod.main([])
        text = out.getvalue()
        self.assertEqual(code, 0, text)
        self.assertNotIn("MISMATCH   ", text)
        self.assertIn("create_lora_training_client", text)
        self.assertIn("returns BackcompatTrainingClientFuture, used through .result()", text)


if __name__ == "__main__":
    unittest.main()

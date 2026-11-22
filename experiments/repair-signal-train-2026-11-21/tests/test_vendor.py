import json
import os
import shutil
import tempfile
import unittest

import _setup  # noqa: F401
import vendor_loader


class VendorTests(unittest.TestCase):
    def test_pinned_hash_matches_the_file(self):
        self.assertEqual(vendor_loader.pinned_hash(), vendor_loader.sha256_file(
            os.path.join(vendor_loader.DEFAULT_VENDOR, "rsig.py")))
        self.assertIsNotNone(vendor_loader.load_rsig().make_instance)

    def test_edited_file_refuses_to_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = os.path.join(tmp, "v")
            shutil.copytree(vendor_loader.DEFAULT_VENDOR, bad)
            with open(os.path.join(bad, "rsig.py"), "ab") as fh:
                fh.write(b"\n")
            with self.assertRaises(vendor_loader.VendorError):
                vendor_loader.load_rsig(bad)

    def test_missing_manifest_entry_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = os.path.join(tmp, "v")
            shutil.copytree(vendor_loader.DEFAULT_VENDOR, bad)
            with open(os.path.join(bad, "MANIFEST.json"), "w") as fh:
                json.dump({"files": {}}, fh)
            with self.assertRaises(vendor_loader.VendorError):
                vendor_loader.load_rsig(bad)

    def test_rsig_sha_is_the_pinned_one(self):
        self.assertEqual(vendor_loader.rsig_sha256(), vendor_loader.pinned_hash())


if __name__ == "__main__":
    unittest.main()

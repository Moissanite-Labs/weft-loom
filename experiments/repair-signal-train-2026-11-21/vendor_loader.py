"""Loads the vendored rsig.py only if its SHA-256 matches the manifest.

The verified bytes are the bytes that get executed, so the file cannot change
between the check and the load. Puzzles, the exact checker and the feedback
texts for arms A and B come only from this module.
"""
import hashlib
import json
import os
import types

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_VENDOR = os.path.join(HERE, "vendor")
_CACHE = {}


class VendorError(Exception):
    """The vendored file is missing or does not match the pinned hash."""


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    with open(path, "rb") as fh:
        return sha256_bytes(fh.read())


def pinned_hash(vendor_dir=None, name="rsig.py"):
    vendor_dir = vendor_dir or DEFAULT_VENDOR
    with open(os.path.join(vendor_dir, "MANIFEST.json"), "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    files = manifest.get("files")
    if not isinstance(files, dict) or name not in files:
        raise VendorError("manifest has no entry for " + name)
    return files[name]


def load_rsig(vendor_dir=None):
    vendor_dir = vendor_dir or DEFAULT_VENDOR
    path = os.path.join(vendor_dir, "rsig.py")
    expected = pinned_hash(vendor_dir)
    with open(path, "rb") as fh:
        data = fh.read()
    actual = sha256_bytes(data)
    if actual != expected:
        raise VendorError("rsig.py hash %s does not match the pinned %s" % (actual, expected))
    key = (os.path.abspath(vendor_dir), actual)
    if key not in _CACHE:
        mod = types.ModuleType("rsig")
        mod.__file__ = path
        exec(compile(data, path, "exec"), mod.__dict__)
        _CACHE[key] = mod
    return _CACHE[key]


def rsig_sha256(vendor_dir=None):
    """Hash of the vendored file after it passed the pin check."""
    load_rsig(vendor_dir)
    return sha256_file(os.path.join(vendor_dir or DEFAULT_VENDOR, "rsig.py"))

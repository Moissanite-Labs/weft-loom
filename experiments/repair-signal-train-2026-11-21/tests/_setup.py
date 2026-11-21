"""Puts the loop folder on sys.path. Tests import this first, so they also run under python3 -I."""
import os
import sys

LOOP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if LOOP not in sys.path:
    sys.path.insert(0, LOOP)

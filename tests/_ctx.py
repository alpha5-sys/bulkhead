"""Put addon/ on sys.path so tests import bulkhead.core without installing anything.

core/ must never import bpy; these tests run in plain CPython.
"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ADDON = os.path.join(_ROOT, "addon")
if _ADDON not in sys.path:
    sys.path.insert(0, _ADDON)

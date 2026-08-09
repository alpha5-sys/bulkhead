"""Bulkhead — panel and greeble generator for Blender.

The bpy-dependent layers import only inside Blender, so that `bulkhead.core` stays
importable in plain CPython for the test suite.
"""
try:
    import bpy as _bpy
except ImportError:
    _bpy = None

if _bpy is not None:
    from .registry import register, unregister  # noqa: F401

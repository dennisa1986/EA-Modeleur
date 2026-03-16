"""Shared cross-cutting utilities.

Modules in this package have no dependencies on any pipeline stage.
Stages may depend on shared; shared must never import from a stage.
"""

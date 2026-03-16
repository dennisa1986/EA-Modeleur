"""Stage 1 — Ingestion.

Reads raw input files (plain text, images/screenshots, PDFs) and produces a
normalised RawContent object.  Downstream stages must not consume raw files
directly; they consume RawContent.
"""

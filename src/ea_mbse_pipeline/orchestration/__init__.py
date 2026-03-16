"""Orchestration — wires all pipeline stages via dependency injection.

The PipelineOrchestrator in pipeline.py is the only place where stages are
composed.  No stage may import another stage directly.
"""

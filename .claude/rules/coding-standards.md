# Coding Standards

## Python conventions
- Python ≥ 3.11. Use `StrEnum`, `match/case`, `X | Y` unions, `Self`.
- `src/` layout — never import from the project root directly.
- Pydantic v2 models for all inter-stage data contracts.
- Each pipeline stage exposes both a `Protocol` (structural) and a `BaseXxx(ABC)` (inheritance).  Keep both in `protocols.py`.
- `raise NotImplementedError` in all stub methods — never `pass` or `...` in non-Protocol bodies.
- No global mutable state. All configuration flows through `settings.py` (pydantic-settings).

## Typing
- `strict = true` in mypy. Every function must have full annotations.
- Use `typing.Protocol` + `@runtime_checkable` for all cross-stage interfaces.
- Avoid `Any` except at system boundaries (file I/O, external APIs).

## Testing
- Mark tests with `@pytest.mark.unit`, `@pytest.mark.integration`, or `@pytest.mark.regression`.
- Unit tests must not touch the filesystem or network.
- Golden files for regression tests live in `tests/regression/fixtures/`.

## Dependencies
- Add runtime deps to `[project.dependencies]` in `pyproject.toml`.
- Add dev/test deps to `[project.optional-dependencies] dev`.
- Use `uv sync --extra dev` to install.

"""Environment-driven configuration (12-factor).

All env vars are prefixed EA_PIPELINE_.
Example .env:
    EA_PIPELINE_LOG_LEVEL=DEBUG
    EA_PIPELINE_EA_VERSION=17.1
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EA_PIPELINE_", env_file=".env")

    # EA target version
    ea_version: str = "17.1"

    # Directory layout
    metamodel_dir: Path = Path("data/raw/metamodel")
    corpus_dir: Path = Path("data/raw/corpus")
    screenshots_dir: Path = Path("data/raw/screenshots")
    processed_dir: Path = Path("data/processed")
    golden_dir: Path = Path("data/golden")
    output_dir: Path = Path("outputs")
    schemas_dir: Path = Path("schemas")

    # Canonical model JSON Schema filename (relative to schemas_dir)
    canonical_schema_filename: str = "canonical_model.schema.json"

    # Logging
    log_level: str = "INFO"


settings = Settings()

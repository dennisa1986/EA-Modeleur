"""Environment-driven configuration (12-factor)."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EA_PIPELINE_", env_file=".env")

    # Paths
    metamodels_dir: Path = Path("metamodels")
    schemas_dir: Path = Path("schemas")
    output_dir: Path = Path("output")

    # EA target version
    ea_version: str = "17.1"

    # Canonical model JSON Schema file name (relative to schemas_dir)
    canonical_schema_filename: str = "canonical_model.schema.json"

    # Logging
    log_level: str = "INFO"


settings = Settings()

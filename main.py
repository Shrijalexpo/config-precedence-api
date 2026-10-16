import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware


BASE_DIR = Path(__file__).resolve().parent
DEFAULTS: dict[str, Any] = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}
ALIASES = {"num_workers": "workers"}

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def normalize_key(key: str) -> str:
    key = key.strip().lower()
    return ALIASES.get(key, key)


def coerce_value(key: str, value: Any) -> Any:
    if key in {"port", "workers"}:
        try:
            return int(value)
        except (TypeError, ValueError) as error:
            raise ValueError(f"{key} must be an integer") from error

    if key == "debug":
        if isinstance(value, bool):
            return value
        normalized = str(value).strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
        raise ValueError("debug must be true/false, 1/0, yes/no, or on/off")

    return str(value)


def load_effective_config(cli_values: list[str]) -> dict[str, Any]:
    config = DEFAULTS.copy()

    environment = os.environ.get("APP_ENV", "development")
    yaml_path = BASE_DIR / f"config.{environment}.yaml"
    if yaml_path.exists():
        with yaml_path.open(encoding="utf-8") as config_file:
            yaml_config = yaml.safe_load(config_file) or {}
        if not isinstance(yaml_config, dict):
            raise ValueError(f"{yaml_path.name} must contain a YAML mapping")
        for key, value in yaml_config.items():
            normalized_key = normalize_key(str(key))
            config[normalized_key] = coerce_value(normalized_key, value)

    dotenv_config = dotenv_values(BASE_DIR / ".env")
    for key, value in dotenv_config.items():
        if value is None:
            continue
        normalized_key = normalize_key(key)
        if normalized_key.startswith("app_"):
            normalized_key = normalize_key(normalized_key.removeprefix("app_"))
        config[normalized_key] = coerce_value(normalized_key, value)

    for key, value in os.environ.items():
        if not key.startswith("APP_") or key == "APP_ENV":
            continue
        normalized_key = normalize_key(key.removeprefix("APP_"))
        config[normalized_key] = coerce_value(normalized_key, value)

    for assignment in cli_values:
        key, separator, value = assignment.partition("=")
        if not separator or not key.strip():
            raise ValueError("each set parameter must have the form key=value")
        normalized_key = normalize_key(key)
        config[normalized_key] = coerce_value(normalized_key, value)

    config["api_key"] = "****"
    return config


@app.get("/effective-config")
def get_effective_config(set: list[str] = Query(default=[])) -> dict[str, Any]:
    try:
        return load_effective_config(set)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

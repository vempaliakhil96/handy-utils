"""Configuration for the Handy Utils CLI."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

from yaml import Loader, dump, load  # type: ignore


@dataclass
class Configuration:
    """Configuration for the Handy Utils CLI."""

    openai_api_key: str
    base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"
    model_kwargs: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    confluence_domain: str = ""
    confluence_api_key: str = ""
    confluence_space_key: str = ""
    confluence_username: str = ""

    def to_yaml(self) -> str:
        """Convert the configuration to a YAML string."""
        return dump(self.__dict__)


def get_config_path() -> Path:
    """Get the path to the configuration file."""
    return Path.home() / ".handy_utils" / "config.yaml"


def load_configuration() -> Configuration:
    """Load the configuration from the file."""
    path = get_config_path()
    if not path.exists():
        return Configuration(openai_api_key=get_openai_api_key())
    with open(path, "r") as f:
        config = load(f, Loader=Loader)
    return Configuration(**config)


def generate_config():
    """Generate a configuration file if it doesn't exist."""
    path = get_config_path()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(Configuration(openai_api_key=get_openai_api_key()).to_yaml())
    else:
        print(f"Config file already exists at {path}")


def view_config():
    """View the configuration."""
    config = load_configuration()
    return config.to_yaml()


def get_openai_api_key() -> str:
    """Get the OpenAI API key from the environment."""
    return os.getenv("OPENAI_API_KEY") or "XXX"

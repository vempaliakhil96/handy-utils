"""Configuration for the Handy Utils CLI."""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from langchain_openai import ChatOpenAI
from yaml import Loader, dump, load


@dataclass
class Configuration:
    """Configuration for the Handy Utils CLI."""

    openai_api_key: str
    base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"
    model_kwargs: Dict[str, Any] = None
    headers: Dict[str, str] = None

    def to_yaml(self) -> str:
        """Convert the configuration to a YAML string."""
        return dump(self.__dict__)


def get_config_path() -> Path:
    """Get the path to the configuration file."""
    return Path.home() / ".handy_utils" / "config.yaml"


def load_configuration() -> Configuration:
    """Load the configuration from the file."""
    path = get_config_path()
    with open(path, "r") as f:
        config = load(f, Loader=Loader)
    return Configuration(**config)


def load_llm(config: Configuration) -> ChatOpenAI:
    """Load the LLM from the configuration."""
    return ChatOpenAI(
        model=config.openai_model,
        **config.model_kwargs,
        default_headers=config.headers,
        api_key=config.openai_api_key,
        base_url=config.base_url,
    )


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

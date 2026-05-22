from pathlib import Path

from core.config import ENV_FILE


def test_env_file_path_is_absolute_and_in_api_dir() -> None:
    assert ENV_FILE.is_absolute()
    assert ENV_FILE.name == ".env"
    assert ENV_FILE.parent.name == "api"
    assert ENV_FILE.parent.parent.name == "apps"

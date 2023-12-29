import json
import typing as t
from pathlib import Path

THIS_FOLDER = Path(__file__).parent


def get_extensions_names():
    return [x.name for x in THIS_FOLDER.iterdir() if x.is_dir() and x.name != '__pycache__']


def read_commands_attributes(commands_attributes_file: str) -> dict:
    commands_attributes = {}
    with open(commands_attributes_file, 'r') as file:
        commands_attributes = json.load(file)
    return commands_attributes


def get_command_attributes_builder(commands_attributes_cache: dict) -> t.Callable[[str], dict]:
    def get_command_attributes(command_name: str) -> dict:
        return commands_attributes_cache.get(command_name, {})
    return get_command_attributes

import json
import logging
import typing as t
from pathlib import Path

from discord.ext import commands

THIS_FOLDER = Path(__file__).parent


logger = logging.getLogger(__name__)


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


def get_command_parameters_builder(commands_attributes_cache: dict) -> t.Callable[[str, str], dict]:
    def get_command_parameters(command_name: str, parameter_name: str) -> dict:
        return commands_attributes_cache.get(command_name, {}).get('parameters', {}).get(parameter_name, {})
    return get_command_parameters


async def manage_extensions(bot: commands.Bot, extensions: list[str], action: str) -> dict[str, list]:
    success = []
    fail = []
    action_mapping = {
        'unload': bot.unload_extension,
        'load': bot.load_extension,
        'reload': bot.reload_extension,
    }

    extension_action = action_mapping.get(action)
    if extension_action is None:
        logger.error('Failed to manage extensions due to invalid action')
        raise ValueError('Failed to manage extensions due to invalid action')
    # TODO: maybe move logging messages from here to the "on_action" of each cog?
    for extension in extensions:
        try:
            await extension_action(f'extensions.{extension}')
            success.append(extension)
            logger.info(f'Extension "{extension}" {action}ed successfully')
        except commands.ExtensionError as error:
            fail.append((extension, error))
            logger.exception(f'Failed to {action} the extension "{extension}" due to error: {error}')

    return {'success': success, 'fail': fail}

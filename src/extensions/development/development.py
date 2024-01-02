import logging
from pathlib import Path

from discord.ext import commands

import custom_errors
from bot_yerak import BotYerak
from settings import settings

from .. import get_command_attributes_builder, get_command_parameters_builder, read_commands_attributes

logger = logging.getLogger(__name__)

THIS_FOLDER = Path(__file__).parent


_commands_attributes = read_commands_attributes(THIS_FOLDER/'commands_attr.json')  # Global cache for config data
get_command_attributes = get_command_attributes_builder(_commands_attributes)
get_command_parameters = get_command_parameters_builder(_commands_attributes)


class Development(commands.Cog, command_attrs=dict(hidden=True)):
    """Useful commands for developers"""

    def __init__(self, bot: BotYerak):
        self.bot = bot

    async def cog_before_invoke(self, ctx: commands.Context) -> None:
        if ctx.author.id not in settings.users_developers_ids:
            # Raise an error so it will not proceed with the command execution
            raise custom_errors.NotAuthorizedUser('Some user tried to execute a developer\'s command')

    @commands.command(**get_command_attributes('reload'))
    async def reload(self, ctx: commands.Context,
        *,
        extensions: str = commands.parameter(**get_command_parameters('reload', 'extensions'))
    ) -> None:
        to_reload = [ext.split('.')[-1] for ext in self.bot.extensions.keys()] if extensions[0] == 'all' else extensions.split(' ')
        action = 'reload'
        result = await self.manage_extensions(to_reload, action)
        await ctx.reply(self._format_extensions_message(result, action))

    @commands.command(**get_command_attributes('load'))
    async def load(self, ctx: commands.Context,
        *,
        extensions: str = commands.parameter(**get_command_parameters('load', 'extensions'))
    ) -> None:
        action = 'load'
        result = await self.manage_extensions(extensions, action)
        await ctx.reply(self._format_extensions_message(result, action))

    @commands.command(**get_command_attributes('unload'))
    async def unload(self, ctx: commands.Context,
        *,
        extensions: str = commands.parameter(**get_command_parameters('unload', 'extensions'))
    ) -> None:
        action = 'unload'
        result = await self.manage_extensions(extensions, action)
        await ctx.reply(self._format_extensions_message(result, action))

    @commands.command(**get_command_attributes('sync'))
    async def sync(self, ctx: commands.Context) -> None:
        synced = await self.bot.tree.sync()
        await ctx.reply(f'Synced {len(synced)} commands successfully')
        logger.info(f'Synced {len(synced)} commands successfully')

    @commands.command(**get_command_attributes('close'))
    async def close(self, ctx: commands.Context) -> None:
        await ctx.reply(f'Are you sure you want to close the bot ["yes" or "no"]?')
        confirmation_message = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author)
        if confirmation_message.content[0].lower() in ['y']:
            await ctx.reply(f'Closing bot')
            logger.info(f'Closing bot')
            await self.bot.close()
        else:
            await ctx.reply(f'Not closing the bot')

    async def manage_extensions(self, extensions: list[str], action: str) -> dict[str, list]:
        success = []
        fail = []
        action_mapping = {
            'unload': self.bot.unload_extension,
            'load': self.bot.load_extension,
            'reload': self.bot.reload_extension,
        }

        extension_action = action_mapping.get(action)
        if extension_action is None:
            logger.error('Failed to manage extensions due to invalid action')
            raise ValueError('Failed to manage extensions due to invalid action')

        for extension in extensions:
            try:
                await extension_action(f'extensions.{extension}')
                success.append(extension)
                logger.info(f'Extension "{extension}" {action}ed successfully')
            except commands.ExtensionError as error:
                fail.append((extension, error))
                logger.error(f'Failed to {action} the extension "{extension}" due to error: {error}')

        return {'success': success, 'fail': fail}

    def _format_extensions_message(self, result: dict[str, list], action: str) -> str:
        success_message = f'Extension(s): "{", ".join(result["success"])}" {action}ed successfully' if result["success"] else ''
        failure_message = f'Failed to {action} the extension(s): "{", ".join([f"{fail[0]} -> {fail[1]}" for fail in result["fail"]])}"' if result["fail"] else ''
        return success_message + failure_message

import logging
from pathlib import Path

from discord.ext import commands

import custom_errors
from bot_yerak import BotYerak
from settings import settings

from .. import get_command_attributes_builder, read_commands_attributes

logger = logging.getLogger(__name__)

THIS_FOLDER = Path(__file__).parent


_commands_attributes = read_commands_attributes(THIS_FOLDER/'commands_attr.json')  # Global cache for config data
get_command_attributes = get_command_attributes_builder(_commands_attributes)


class Development(commands.Cog, command_attrs=dict(hidden=True)):
    """Useful commands for developers"""

    def __init__(self, bot: BotYerak):
        self.bot = bot

    async def cog_before_invoke(self, ctx: commands.Context) -> None:
        if ctx.author.id not in settings.users_developers_ids:
            # Raise an error so it will not proceed with the command execution
            raise custom_errors.NotAuthorizedUser('Some user tried to execute a developer\'s command')

    @commands.command(**get_command_attributes('reload'))
    async def reload(self, ctx: commands.Context, *, extension: str) -> None:
        extension = extension.lower()
        try:
            await self.bot.reload_extension(f'extensions.{extension}')
            await ctx.reply(f'Extension {extension} reloaded successfully')
            logger.info(f'Extension "{extension}" reloaded successfully')
        except Exception as error:
            await ctx.reply(f'Failed to reload the extension "{extension}" due to error: {error}')
            logger.error(f'Failed to reload the extension "{extension}" due to error: {error}')

    @commands.command(**get_command_attributes('sync'))
    async def sync(self, ctx: commands.Context) -> None:
        synced = await self.bot.tree.sync()
        await ctx.reply(f'Synced {len(synced)} commands successfully')
        logger.info(f'Synced {len(synced)} commands successfully')
        
    @commands.command(**get_command_attributes('close'))
    async def close(self, ctx: commands.Context) -> None:
        await ctx.reply(f'Closing bot')
        logger.info(f'Closing bot')
        await self.bot.close()
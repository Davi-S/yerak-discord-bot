import logging
from pathlib import Path

from discord.ext import commands

import bot_yerak as by
import custom_context as cc
import custom_errors as ce
import extensions as exts
from settings import settings

logger = logging.getLogger(__name__)

THIS_FOLDER = Path(__file__).parent


_commands_attributes = exts.read_commands_attributes(THIS_FOLDER/'commands_attr.json')  # Global cache for config data
get_command_attributes = exts.get_command_attributes_builder(_commands_attributes)
get_command_parameters = exts.get_command_parameters_builder(_commands_attributes)


class Development(commands.Cog, command_attrs=dict(hidden=True)):
    """Useful commands for developers"""

    def __init__(self, bot: by.BotYerak) -> None:
        self.bot = bot
        
    def cog_load(self) -> None:
        # Delete the global command attributes cache. After the cog has loaded, it is not needed anymore and can be deleted to save memory
        global _commands_attributes
        del _commands_attributes

    async def cog_before_invoke(self, ctx: cc.CustomContext) -> None:
        if ctx.author.id not in settings.users_developers_ids:
            # Raise an error so it will not proceed with the command execution
            raise ce.NotAuthorizedUser('Some user tried to execute a developer\'s command')

    @commands.command(**get_command_attributes('reload'))
    async def reload(self, ctx: cc.CustomContext, *,
        extensions: str = commands.parameter(**get_command_parameters('reload', 'extensions'))
    ) -> None:
        to_reload = [ext.split('.')[-1] for ext in self.bot.extensions.keys()] if extensions[0] == 'all' else extensions.split(' ')
        action = 'reload'
        result = await exts.manage_extensions(self.bot, to_reload, action)
        await ctx.reply(self._format_extensions_message(result, action))

    @commands.command(**get_command_attributes('load'))
    async def load(self, ctx: cc.CustomContext, *,
        extensions: str = commands.parameter(**get_command_parameters('load', 'extensions'))
    ) -> None:
        action = 'load'
        result = await exts.manage_extensions(self.bot, [extensions], action)
        await ctx.reply(self._format_extensions_message(result, action))

    @commands.command(**get_command_attributes('unload'))
    async def unload(self, ctx: cc.CustomContext, *,
        extensions: str = commands.parameter(**get_command_parameters('unload', 'extensions'))
    ) -> None:
        action = 'unload'
        result = await exts.manage_extensions(self.bot, [extensions], action)
        await ctx.reply(self._format_extensions_message(result, action))

    @commands.command(**get_command_attributes('sync'))
    async def sync(self, ctx: cc.CustomContext) -> None:
        synced = await self.bot.tree.sync()
        await ctx.reply(f'Synced {len(synced)} commands successfully')
        logger.info(f'Synced {len(synced)} commands successfully')

    @commands.command(**get_command_attributes('close'))
    async def close(self, ctx: cc.CustomContext) -> None:
        await ctx.reply('Are you sure you want to close the bot ["yes" or "no"]?')
        confirmation_message = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author)
        if confirmation_message.content[0].lower() in ['y']:
            await ctx.reply('Closing bot')
            await self.bot.close()
        else:
            await ctx.reply('Not closing the bot')

    def _format_extensions_message(self, result: dict[str, list], action: str) -> str:
        success_message = f'Extension(s): "{", ".join(result["success"])}" {action}ed successfully' if result["success"] else ''
        failure_message = f'Failed to {action} the extension(s): "{", ".join([f"{fail[0]} -> {fail[1]}" for fail in result["fail"]])}"' if result["fail"] else ''
        return success_message + failure_message

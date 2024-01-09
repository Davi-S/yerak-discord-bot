import discord
from discord import app_commands
from discord.ext import commands

import bot_yerak as by

from .help_cls import MyHelp

_help_command_attrs = {
    "help": "Display information about available categories, commands and other useful information",
    "brief": "Show a help message"
}


class Help(commands.Cog):
    """The a place for the help command"""

    def __init__(self, bot: by.BotYerak):
        self.bot = bot
        # Set the custom help command
        self._original_help_command = bot.help_command
        self.bot.help_command = MyHelp(command_attrs=_help_command_attrs)
        self.bot.help_command.cog = self

    @app_commands.command(description=_help_command_attrs['help'])
    async def help(self, interaction: discord.Interaction, on: str = None):
        context = await self.bot.get_context(interaction)
        await self.bot.help_command.command_callback(context, command=on)

    def cog_unload(self):
        self.bot.help_command = self._original_help_command

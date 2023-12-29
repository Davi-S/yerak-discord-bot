from discord.ext import commands

from bot_yerak import BotYerak

from .help_cls import MyHelp


class Help(commands.Cog):
    """The a place for the help command"""

    def __init__(self, bot: BotYerak):
        self.bot = bot
        # Set the custom help command
        self._original_help_command = bot.help_command
        self.bot.help_command = MyHelp()
        self.bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command

import logging
from pathlib import Path

from discord.ext import commands

from bot_yerak import BotYerak

from .. import get_command_attributes_builder, read_commands_attributes

logger = logging.getLogger(__name__)

THIS_FOLDER = Path(__file__).parent


_commands_attributes = read_commands_attributes(THIS_FOLDER/'commands_attr.json')  # Global cache for config data
get_command_attributes = get_command_attributes_builder(_commands_attributes)


class Miscellaneous(commands.Cog):
    """Commands that do not fit any other category"""

    def __init__(self, bot: BotYerak) -> None:
        self.bot = bot

    @commands.command(**get_command_attributes('ping'))
    async def ping(self, ctx: commands.Context) -> None:
        await ctx.reply(f'Pong! -> {int(self.bot.latency * 1000)}ms')

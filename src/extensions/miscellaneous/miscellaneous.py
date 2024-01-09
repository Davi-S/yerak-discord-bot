import logging
from pathlib import Path

from discord.ext import commands

import bot_yerak as by
import custom_context as cc
import extensions as exts

logger = logging.getLogger(__name__)

THIS_FOLDER = Path(__file__).parent


_commands_attributes = exts.read_commands_attributes(THIS_FOLDER/'commands_attr.json')  # Global cache for config data
get_command_attributes = exts.get_command_attributes_builder(_commands_attributes)


class Miscellaneous(commands.GroupCog):
    """Commands that do not fit any other category"""

    def __init__(self, bot: by.BotYerak) -> None:
        self.bot = bot
        
    def cog_load(self) -> None:
        # Delete the global command attributes cache. After the cog has loaded, it is not needed anymore and can be deleted to save memory
        global _commands_attributes
        del _commands_attributes

    @commands.hybrid_command(**get_command_attributes('ping'))
    async def ping(self, ctx: cc.CustomContext) -> None:
        await ctx.reply(f'Pong! -> {int(self.bot.latency * 1000)}ms')
        
    @commands.hybrid_command(**get_command_attributes('hello'))
    async def hello(self, ctx: cc.CustomContext) -> None:
        await ctx.send(f'Hi, {ctx.author.mention}')

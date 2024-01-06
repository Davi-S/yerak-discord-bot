import logging
import math
from pathlib import Path

import discord
import youtube_dl
from discord.ext import commands

import extensions as exts
from bot_yerak import BotYerak

logger = logging.getLogger(__name__)

THIS_FOLDER = Path(__file__).parent


_commands_attributes = exts.read_commands_attributes(THIS_FOLDER/'commands_attr.json')  # Global cache for config data
get_command_attributes = exts.get_command_attributes_builder(_commands_attributes)
class Music(commands.GroupCog):
    """Play songs on a voice channel"""
        
    def __init__(self, bot: BotYerak):
        self.bot = bot


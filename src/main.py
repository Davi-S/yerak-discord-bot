# SETUP LOGGING
import logging
import logging.config

from settings.logging_config import dict_config

logging.config.dictConfig(dict_config)

# IMPORTS
import asyncio

import discord
from discord.ext import commands

import bot_yerak as by
import extensions
from settings import settings

logger = logging.getLogger(__name__)


async def main() -> int:
    async with by.BotYerak(
        command_prefix=commands.when_mentioned_or(*settings.prefixes),
        help_command=commands.MinimalHelpCommand(),
        intents=discord.Intents.all(),
        initial_extensions=extensions.get_extensions_names()
    ) as bot:
        await bot.start(settings.token)

if __name__ == '__main__':
    logger.info('Running main function')
    asyncio.run(main())

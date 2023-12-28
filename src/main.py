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
    intents = discord.Intents.default()
    intents.message_content = True
    async with by.BotYerak(
        command_prefix=commands.when_mentioned_or(*settings.prefixes),
        help_command=commands.MinimalHelpCommand(),
        intents=intents
    ) as bot:

        # Dynamically load extensions
        for extension in extensions.get_extensions_name():
            try:
                await bot.load_extension(f'extensions.{extension}')
                logger.info(f'Extension "{extension}" loaded successfully')
            except Exception as error:
                logger.error(f'Error while loading the extension "{extension}". {error}')
        await bot.start(settings.token)

if __name__ == '__main__':
    asyncio.run(main())

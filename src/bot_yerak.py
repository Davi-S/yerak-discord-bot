import logging

from discord.ext import commands

logger = logging.getLogger(__name__)


class BotYerak(commands.Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def on_ready(self) -> None:
        logger.info(f'Logged in as "{self.user.name}"')

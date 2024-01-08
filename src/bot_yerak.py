import asyncio
import logging
import signal

from discord.ext import commands

import custom_context as cc
import extensions as exts
from settings import settings

logger = logging.getLogger(__name__)


class BotYerak(commands.Bot):
    def __init__(self, *args, initial_extensions: list[str], **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.add_exit_handler()
        self.initial_extensions = initial_extensions

    def add_exit_handler(self) -> None:
        """Register a signal handler for termination signals (usually ctrl+c)"""
        signal.signal(signal.SIGINT, lambda *args, **kwargs: asyncio.create_task(self.close(*args, **kwargs)))

    async def close(self, *args, **kwargs) -> None:
        """Exit handler for termination signals"""
        # TODO: fix "Unclosed connector" and "Unclosed client session" error
        logger.warning('Closing bot')
        await super().close()

    async def setup_hook(self) -> None:
        """Setup the bot"""
        await exts.manage_extensions(self, self.initial_extensions, 'load')

        # # Sync application commands with testing guilds
        # for guild_id in settings.guilds_developers_ids:
        #     guild = await self.fetch_guild(guild_id)
        #     # Copy in the global commands to test, and sync to the testing guild.
        #     self.tree.copy_global_to(guild=guild)
        #     await self.tree.sync(guild=guild)
        #     logger.info(f'Synced with testing guild "{guild.name}"')

    async def on_command(self, ctx: commands.Context) -> None:
        """Called when a command is about to be invoked"""
        # Logs all command calls
        logger.debug(f'Command "{ctx.command.qualified_name}" called on guild "{ctx.guild.name}" by the user "{ctx.author.name}"')

    async def get_context(self, message, *, cls=cc.CustomContext): 
        return await super().get_context(message, cls=cls)

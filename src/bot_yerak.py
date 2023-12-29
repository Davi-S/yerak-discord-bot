import asyncio
import logging
import signal
from discord.ext import commands
from settings import settings

logger = logging.getLogger(__name__)


class BotYerak(commands.Bot):
    def __init__(self, *args, initial_extensions: list[str], **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.add_exit_handler()
        self.initial_extensions = initial_extensions

    def add_exit_handler(self) -> None:
        # Register a signal handler for termination signals (usually ctrl+c)
        signal.signal(signal.SIGINT, lambda *args, **kwargs: asyncio.create_task(self.exit_handler(*args, **kwargs)))
        
    async def exit_handler(self, *args, **kwargs) -> None:
        # TODO: fix "Unclosed connector" and "Unclosed client session" error
        await self.close()
        
    async def setup_hook(self) -> None:
        # Load extensions
        for extension in self.initial_extensions:
            try:
                await self.load_extension(f'extensions.{extension}')
                logger.info(f'Extension "{extension}" loaded successfully')
            except Exception as error:
                logger.error(f'Error while loading the extension "{extension}". {error}')
        
        # # Sync application commands with testing guilds
        # for guild_id in settings.guilds_developers_ids:
        #     guild = await self.fetch_guild(guild_id)
        #     # Copy in the global commands to test, and sync to the testing guild.
        #     self.tree.copy_global_to(guild=guild)
        #     await self.tree.sync(guild=guild)
        #     logger.info(f'Synced with testing guild "{guild.name}"')
import bot_yerak as by

from .help_cog import Help


async def setup(bot: by.BotYerak) -> None:
    await bot.add_cog(Help(bot))
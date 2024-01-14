import bot_yerak as by

from .error_handler import ErrorHandler


async def setup(bot: by.BotYerak) -> None:
    await bot.add_cog(ErrorHandler(bot))
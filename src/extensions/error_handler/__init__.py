import bot_yerak as by

from .error_handler import ErrorHandler


async def setup(bot: by.BotYerak):
    await bot.add_cog(ErrorHandler(bot))
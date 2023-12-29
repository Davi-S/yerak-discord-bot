from bot_yerak import BotYerak
from .error_handler import ErrorHandler

async def setup(bot: BotYerak):
    await bot.add_cog(ErrorHandler(bot))
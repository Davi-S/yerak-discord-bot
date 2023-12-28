from bot_yerak import BotYerak

from .development import Development


async def setup(bot: BotYerak):
    await bot.add_cog(Development(bot))

from bot_yerak import BotYerak

from .music import Music


async def setup(bot: BotYerak) -> None:
    await bot.add_cog(Music(bot))

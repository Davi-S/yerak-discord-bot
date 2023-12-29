from bot_yerak import BotYerak

from .miscellaneous import Miscellaneous


async def setup(bot: BotYerak) -> None:
    await bot.add_cog(Miscellaneous(bot))

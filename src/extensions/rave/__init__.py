from bot_yerak import BotYerak

from .rave import Rave


async def setup(bot: BotYerak) -> None:
    await bot.add_cog(Rave(bot))

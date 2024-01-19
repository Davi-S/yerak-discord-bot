import bot_yerak as by

from .rave import Rave


async def setup(bot: by.BotYerak) -> None:
    await bot.add_cog(Rave(bot))

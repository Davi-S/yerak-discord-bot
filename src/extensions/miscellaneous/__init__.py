import bot_yerak as by

from .miscellaneous import Miscellaneous


async def setup(bot: by.BotYerak) -> None:
    await bot.add_cog(Miscellaneous(bot))

import bot_yerak as by

from .music import Music


async def setup(bot: by.BotYerak) -> None:
    await bot.add_cog(Music(bot))

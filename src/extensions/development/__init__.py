import bot_yerak as by

from .development import Development


async def setup(bot: by.BotYerak) -> None:
    await bot.add_cog(Development(bot))

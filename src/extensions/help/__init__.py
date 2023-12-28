from bot_yerak import BotYerak

from .help_cog import Help


async def setup(bot: BotYerak) -> None:
    await bot.add_cog(Help(bot))
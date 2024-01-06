from discord.ext import commands


class NotAuthorizedUser(commands.CommandError):
    pass


class YTDLError(Exception):
    pass

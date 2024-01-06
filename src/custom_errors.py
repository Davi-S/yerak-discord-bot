from discord.ext import commands


class NotAuthorizedUser(commands.CommandError):
    pass

# TODO: make better errors
class YTDLError(Exception):
    pass


class VoiceError(Exception):
    pass
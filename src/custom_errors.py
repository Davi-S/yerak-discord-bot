from discord.ext import commands
import discord


class NotAuthorizedUser(commands.CommandError):
    pass


class YTDLError(commands.CommandError):
    pass


class VoiceError(commands.CommandError):
    pass


class UnhandledError(commands.CommandError):
    pass
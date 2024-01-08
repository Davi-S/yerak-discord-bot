from discord.ext import commands
from voice_client import CustomVoiceClient

# TODO: replace all commands.context with this custom context 
class CustomContext(commands.Context):
    voice_client: CustomVoiceClient
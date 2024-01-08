from discord.ext import commands
import custom_voice_client as vc 

# TODO: replace all commands.context with this custom context 
class CustomContext(commands.Context):
    voice_client: vc.CustomVoiceClient
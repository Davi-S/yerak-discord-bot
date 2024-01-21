from discord.ext import commands

import custom_voice_client as cvc


class CustomContext(commands.Context):
    voice_client: cvc.CustomVoiceClient

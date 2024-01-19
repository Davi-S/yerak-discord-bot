from discord.ext import commands

import custom_voice_client as vc


class CustomContext(commands.Context):
    voice_client: vc.CustomVoiceClient
from __future__ import annotations  # TODO: remove this
from discord.ext import commands

# TODO: replace commands.context with this custom context 
class CustomContext(commands.Context):
    voice_client: CustomVoiceClient  # type: ignore # TODO: fix this hint
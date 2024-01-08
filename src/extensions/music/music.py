import logging
from pathlib import Path

from discord.ext import commands

import custom_context as cc
import extensions as exts
import voice_client as vc
from bot_yerak import BotYerak

logger = logging.getLogger(__name__)

THIS_FOLDER = Path(__file__).parent
FFMPEG_PATH = THIS_FOLDER/'ffmpeg.exe'

_commands_attributes = exts.read_commands_attributes(THIS_FOLDER/'commands_attr.json')  # Global cache for config data
get_command_attributes = exts.get_command_attributes_builder( _commands_attributes)

# TODO: there is a logging error some times


class Music(commands.GroupCog):
    """Play songs on a voice channel"""

    def __init__(self, bot: BotYerak):
        self.bot = bot

    @commands.hybrid_command(**get_command_attributes('join'))
    async def join(self, ctx: cc.CustomContext):
        destination = ctx.author.voice.channel
        if ctx.voice_client is None:
            # Attention to the custom class in the connect function.
            # This class is now the type of ctx.voice_client
            await destination.connect(cls=vc.CustomVoiceClient)
        else:
            await ctx.voice_client.move_to(destination)
        await ctx.reply(f'Joined channel {destination.name}')

    @commands.hybrid_command(**get_command_attributes('leave'))
    async def leave(self, ctx: cc.CustomContext):
        if voice := ctx.voice_client:
            await voice.disconnect()
            await ctx.reply('Disconnected')
            return
        await ctx.reply('Not connected to any voice channel')

    @commands.hybrid_command(**get_command_attributes('play'))
    async def play(self, ctx: cc.CustomContext, *, search: str):
        if not ctx.voice_client:
            await ctx.invoke(self.join)

        async with ctx.typing():
            # TODO: Remove this AudioSource from here. The CustomVoiceClient should be responsible for handling all
            await ctx.voice_client.queue.put((ctx, search))
            await ctx.reply(f'Enqueued {search}')

    @commands.hybrid_command(**get_command_attributes('pause'))
    async def pause(self, ctx: cc.CustomContext):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.reply('Paused')

    @commands.hybrid_command(**get_command_attributes('resume'))
    async def resume(self, ctx: cc.CustomContext):
        if ctx.voice_client and not ctx.voice_client.is_playing():
            ctx.voice_client.resume()
            await ctx.reply('Resumed')

    @commands.hybrid_command(**get_command_attributes('stop'))
    async def stop(self, ctx: cc.CustomContext):
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.reply('Stopped')

    @join.before_invoke
    @play.before_invoke
    async def ensure_voice_state(self, ctx: cc.CustomContext):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('You are not connected to any voice channel.')

import logging
from pathlib import Path

from discord.ext import commands

import bot_yerak as by
import custom_context as cc
import custom_voice_client as vc
import extensions as exts

logger = logging.getLogger(__name__)

THIS_FOLDER = Path(__file__).parent
FFMPEG_PATH = THIS_FOLDER/'ffmpeg.exe'

_commands_attributes = exts.read_commands_attributes(THIS_FOLDER/'commands_attr.json')  # Global cache for config data
get_command_attributes = exts.get_command_attributes_builder( _commands_attributes)

# TODO: there is a logging error some times
# TODO: COMMANDS
# ☑ enter
# ☑ leave
# ☑ play/enqueue
# addplaylist
# ☑ pause
# ☑ resume
# stop
# skip
# volume
# goto 
# lyrics
# loop
# nowplaying
# queue
# clear
# shuffle
# delete

class Music(commands.GroupCog):
    """Play songs on a voice channel"""

    def __init__(self, bot: by.BotYerak):
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
        await ctx.voice_client.disconnect()
        await ctx.reply('Disconnected')

    @commands.hybrid_command(**get_command_attributes('play'))
    async def play(self, ctx: cc.CustomContext, *, search: str):
        async with ctx.typing():
            # Put the audio in the queue. If this is the only audio in the queue, it will start automatically
            await ctx.voice_client.queue.put((ctx, search))
        # TODO: get the audio that was just added to show its title
        await ctx.reply(f'Enqueued {search}')

    @commands.hybrid_command(**get_command_attributes('pause'))
    async def pause(self, ctx: cc.CustomContext):
        ctx.voice_client.pause()
        await ctx.reply('Paused')

    @commands.hybrid_command(**get_command_attributes('resume'))
    async def resume(self, ctx: cc.CustomContext):
        ctx.voice_client.resume()
        await ctx.reply('Resumed')
    
    @commands.hybrid_command(**get_command_attributes('stop'))
    async def stop(self, ctx: cc.CustomContext):
        pass
    
    # TODO: use "checks"
    # TODO: handle errors raised here
    @join.before_invoke
    async def ensure_author_voice(self, ctx: cc.CustomContext):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('You are not connected to a voice channel.')

    @play.before_invoke
    @leave.before_invoke
    async def ensure_bot_voice(self, ctx: cc.CustomContext):
        if not ctx.voice_client:
            raise commands.CommandError('Bot it not connected to a voice channel')
    
    @pause.before_invoke
    async def ensure_bot_playing(self, ctx: cc.CustomContext):
        voice = ctx.voice_client
        if (not voice) or (not voice.is_playing()):
            raise commands.CommandError('Bot it not playing anything')
    
    @resume.before_invoke
    async def ensure_bot_paused(self, ctx: cc.CustomContext):
        voice = ctx.voice_client
        if (not voice) or (not ctx.voice_client.is_paused()):
            raise commands.CommandError('Bot it not paused')
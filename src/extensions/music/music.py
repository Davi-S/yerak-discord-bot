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
get_command_attributes = exts.get_command_attributes_builder(_commands_attributes)


# CHECKS
def ensure_author_voice():
    def predicate(ctx: cc.CustomContext):
        return ctx.author.voice and ctx.author.voice.channel
    return commands.check(predicate)


def ensure_bot_voice():
    def predicate(ctx: cc.CustomContext):
        return ctx.voice_client
    return commands.check(predicate)


def ensure_bot_playing():
    def predicate(ctx: cc.CustomContext):
        voice = ctx.voice_client
        return voice and voice.is_playing()
    return commands.check(predicate)


def ensure_bot_paused():
    def predicate(ctx: cc.CustomContext):
        voice = ctx.voice_client
        return voice and ctx.voice_client.is_paused()
    return commands.check(predicate)


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
    @ensure_author_voice()
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
    @ensure_bot_voice()
    async def leave(self, ctx: cc.CustomContext):
        await ctx.voice_client.disconnect()
        await ctx.reply('Disconnected')

    @commands.hybrid_command(**get_command_attributes('play'))
    @ensure_bot_voice()
    async def play(self, ctx: cc.CustomContext, *, search: str):
        async with ctx.typing():
            # Put the audio in the queue. If this is the only audio in the queue, it will start automatically
            await ctx.voice_client.queue.put((ctx, search))
        # TODO: get the audio that was just added to show its title
        await ctx.reply(f'Enqueued {search}')

    @commands.hybrid_command(**get_command_attributes('pause'))
    @ensure_bot_playing()
    async def pause(self, ctx: cc.CustomContext):
        ctx.voice_client.pause()
        await ctx.reply('Paused')

    @commands.hybrid_command(**get_command_attributes('resume'))
    @ensure_bot_paused()
    async def resume(self, ctx: cc.CustomContext):
        ctx.voice_client.resume()
        await ctx.reply('Resumed')

    @commands.hybrid_command(**get_command_attributes('stop'))
    async def stop(self, ctx: cc.CustomContext):
        pass

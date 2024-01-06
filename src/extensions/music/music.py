import asyncio
import functools
import logging
from pathlib import Path

import discord
# import youtube_dl
import yt_dlp as youtube_dl
from discord.ext import commands

import custom_errors as ce
import extensions as exts
from bot_yerak import BotYerak

logger = logging.getLogger(__name__)

THIS_FOLDER = Path(__file__).parent
FFMPEG_PATH = THIS_FOLDER/'ffmpeg.exe'

_commands_attributes = exts.read_commands_attributes(THIS_FOLDER/'commands_attr.json')  # Global cache for config data
get_command_attributes = exts.get_command_attributes_builder(_commands_attributes)


YTDL_OPTIONS = {
    'audioformat': 'mp3',
    'extractaudio': True,
    'format': 'bestaudio/best',
    'nocheckcertificate': True,
    'noplaylist': True,
    'quiet': True,
    'restrictfilenames': True,
    'default_search': 'ytsearch',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}


async def create_PCMVolumeTransformer(query: str):
    loop = asyncio.get_event_loop()

    with youtube_dl.YoutubeDL(YTDL_OPTIONS) as ytdl:
        partial = functools.partial(ytdl.extract_info, query, download=False)
        data = await loop.run_in_executor(None, partial)

    if data is None:
        raise ce.YTDLError(f'Couldn\'t find anything that matches "{query}"')

    return discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(data['url'], executable=str(FFMPEG_PATH), **FFMPEG_OPTIONS), volume=0.5)


class Music(commands.GroupCog):
    """Play songs on a voice channel"""

    def __init__(self, bot: BotYerak):
        self.bot = bot

    @commands.hybrid_command(**get_command_attributes('join'))
    async def join(self, ctx: commands.Context):
        destination = ctx.author.voice.channel
        if ctx.guild.voice_client is None:
            await destination.connect()
        else:
            await ctx.guild.voice_client.move_to(destination)
        await ctx.reply(f'Joined channel {destination.name}')

    @commands.hybrid_command(**get_command_attributes('leave'))
    async def leave(self, ctx: commands.Context):
        if voice := ctx.guild.voice_client:
            await voice.disconnect()
            await ctx.reply('Disconnected')
            return
        await ctx.reply('Not connected to any voice channel')

    @commands.hybrid_command(**get_command_attributes('play'))
    async def play(self, ctx: commands.Context, *, query: str):
        if not ctx.guild.voice_client:
            await ctx.invoke(self.join)

        async with ctx.typing():
            source = await create_PCMVolumeTransformer(query)
            ctx.guild.voice_client.play(source)
            await ctx.reply(f'Playing {query}')

    @join.before_invoke
    @play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('You are not connected to any voice channel.')

    @commands.hybrid_command(**get_command_attributes('set_volume'))
    async def set_volume(self, ctx: commands.Context, *, volume: int):
        if not ctx.guild.voice_client:
            return await ctx.reply('Nothing being played at the moment.')
        if 0 > volume > 100:
            return await ctx.reply('Volume must be between 0 and 100')
        ctx.guild.voice_client.source.volume = volume / 100
        await ctx.reply(f'Volume of the player set to {volume}%')

    @commands.hybrid_command(**get_command_attributes('pause'))
    async def pause(self, ctx: commands.Context):
        if ctx.guild.voice_client and ctx.guild.voice_client.is_playing():
            ctx.guild.voice_client.pause()
            await ctx.reply('Paused')

    @commands.hybrid_command(**get_command_attributes('resume'))
    async def resume(self, ctx: commands.Context):
        if ctx.guild.voice_client and not ctx.guild.voice_client.is_playing():
            ctx.guild.voice_client.resume()
            await ctx.reply('Resumed')

    @commands.hybrid_command(**get_command_attributes('stop'))
    async def stop(self, ctx: commands.Context):
        if ctx.guild.voice_client.is_playing():
            ctx.guild.voice_client.stop()
            await ctx.reply('Stopped')


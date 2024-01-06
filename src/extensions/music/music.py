import asyncio
import collections
import functools
import logging
import random
import typing as t
from pathlib import Path

import discord
# import youtube_dl
import yt_dlp as youtube_dl
from async_timeout import timeout
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
    'executable': str(FFMPEG_PATH),
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}


class AudioSource(discord.PCMVolumeTransformer):
    def __init__(self, original: discord.FFmpegPCMAudio, volume: float, *, source_data: dict = None):
        super().__init__(original, volume)

        self.requester = source_data.get('requester')
        self.channel = source_data.get('channel')
        self.data = source_data
        self.uploader = source_data.get('uploader')
        self.uploader_url = source_data.get('uploader_url')
        date = source_data.get('upload_date')
        self.upload_date = f'{date[6:8]}.{date[4:6]}.{date[:4]}'
        self.title = source_data.get('title')
        self.thumbnail = source_data.get('thumbnail')
        self.description = source_data.get('description')
        self.duration = self.parse_duration(int(source_data.get('duration')))
        self.tags = source_data.get('tags')
        self.url = source_data.get('webpage_url')
        self.views = source_data.get('view_count')
        self.likes = source_data.get('like_count')
        self.dislikes = source_data.get('dislike_count')
        self.stream_url = source_data.get('url')

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, ytdl_options: dict = YTDL_OPTIONS, ffmpeg_options: dict = FFMPEG_OPTIONS, volume: float = 0.5):
        # TODO: check for errors in this method
        with youtube_dl.YoutubeDL(ytdl_options) as ytdl:
            partial = functools.partial(ytdl.extract_info, search, download=False)
            data = await asyncio.get_event_loop().run_in_executor(None, partial)

        if data is None:
            raise ce.YTDLError(f'Couldn\'t find anything that matches "{search}"')

        context_data = {
            'requester': ctx.author,
            'channel': ctx.channel
        }

        return cls(discord.FFmpegPCMAudio(data['url'], **ffmpeg_options), volume=volume, source_data=data | context_data)

    @staticmethod
    def parse_duration(duration: int):
        units = [
            ('days', 24 * 60 * 60),
            ('hours', 60 * 60),
            ('minutes', 60),
            ('seconds', 1)
        ]
        times = []
        for unit, seconds_in_unit in units:
            value, duration = divmod(duration, seconds_in_unit)
            if value > 0:
                times.append(f'{value} {unit}' if value == 1 else f'{value} {unit}s')
        return ', '.join(times)


class AudioQueue(asyncio.Queue[AudioSource]):
    def _init(self, maxsize) -> None:
        # TODO: check the maxsize
        # This is here for type-hints/IDE reasons
        self._queue: t.Deque[AudioSource] = collections.deque()

    def _put(self, item: AudioSource) -> None:
        if not isinstance(item, AudioSource):
            raise TypeError('AudioQueue can only hold AudioSource objects')
        self._queue.append(item)

    def clear(self) -> None:
        self._queue.clear()

    def shuffle(self) -> None:
        random.shuffle(self._queue)

    def remove(self, index: int) -> None:
        if 0 <= index < len(self._queue):
            del self._queue[index]
        else:
            raise IndexError("Index out of range")


class CustomVoiceClient(discord.VoiceClient):
    def __init__(self, client, channel,
            timeout: int = 180,
            on_play_callback: t.Callable[[t.Any, t.Any], t.Awaitable[t.Any]] = None,
            on_play_callback_kwargs: dict = None
    ) -> None:
        super().__init__(client, channel)
        self.queue = AudioQueue(20)
        self.next_event = asyncio.Event()
        self.looping = False
        self.audio_player_task = self.client.loop.create_task(self.audio_player())
        self.timeout = timeout
        self.current_audio: AudioSource = None

        if on_play_callback is None:
            on_play_callback = self._default_on_play_callback
        if on_play_callback_kwargs is None:
            on_play_callback_kwargs = {}
        self.on_play_callback = on_play_callback
        self.on_play_kwargs = on_play_callback_kwargs

    @property
    def volume(self):
        return self.current_audio.volume

    @volume.setter
    def volume(self, value: float):
        self.current_audio.volume = value

    async def audio_player(self):
        while True:
            self.next_event.clear()
            if not self.looping:
                # Try to get the next song within 3 minutes.
                # If no song is added to the queue in time, the player will disconnect due to performance reasons.
                try:
                    async with timeout(self.timeout):
                        self.current_audio = await self.queue.get()
                except asyncio.TimeoutError:
                    self.client.loop.create_task(self.disconnect())
                    return

            # TODO: check and understand this volume part
            # self.current_audio.volume = self.volume
            self.play(self.current_audio, after=self.play_next)
            await self.on_play_callback(**self.on_play_kwargs)
            await self.next_event.wait()

    def play_next(self, error=None):
        if error:
            raise ce.VoiceError(str(error))
        self.next_event.set()

    def skip(self):
        if self.is_playing():
            # Stopping the current audio will trigger the play_next method and start the next song if any available on the queue
            self.stop()

    async def disconnect(self, *, force: bool = False) -> None:
        self.queue.clear()
        return await super().disconnect(force=force)

    async def _default_on_play_callback(self, **kwargs):
        # TODO add args too (not only kwargs)
        return

    def __del__(self):
        self.audio_player_task.cancel()


class Music(commands.GroupCog):
    """Play songs on a voice channel"""

    def __init__(self, bot: BotYerak):
        self.bot = bot

    @commands.hybrid_command(**get_command_attributes('join'))
    async def join(self, ctx: commands.Context):
        destination = ctx.author.voice.channel
        if ctx.guild.voice_client is None:
            # Attention to the custom class in the connect function.
            # This class is now the type of ctx.guild.voice_client
            await destination.connect(cls=CustomVoiceClient)
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
    async def play(self, ctx: commands.Context, *, search: str):
        if not ctx.guild.voice_client:
            await ctx.invoke(self.join)

        async with ctx.typing():
            audio_source = await AudioSource.create_source(ctx, search)
            await ctx.guild.voice_client.queue.put(audio_source)
            await ctx.reply(f'Enqueued {search}')

    @commands.hybrid_command(**get_command_attributes('set_volume'))
    async def set_volume(self, ctx: commands.Context, volume: int):
        if not ctx.guild.voice_client:
            return await ctx.reply('Nothing being played at the moment.')
        if 0 > volume > 100:
            return await ctx.reply('Volume must be between 0 and 100')
        ctx.guild.voice_client.volume = volume / 100
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

    @join.before_invoke
    @play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('You are not connected to any voice channel.')


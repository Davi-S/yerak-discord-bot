import asyncio
import collections
import functools
import random
import typing as t
from pathlib import Path

import discord
# import youtube_dl
import yt_dlp as youtube_dl
from async_timeout import timeout
from discord.ext import commands

import custom_errors as ce

THIS_FOLDER = Path(__file__).parent
FFMPEG_PATH = THIS_FOLDER/'ffmpeg.exe'

FFMPEG_OPTIONS = {
    'executable': str(FFMPEG_PATH),
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

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


class CustomVoiceClient(discord.VoiceClient):
    def __init__(self, client, channel,
            timeout: int = 180,
            on_play_callback: t.Callable[[t.Any, t.Any], t.Awaitable[t.Any]] = None,
            on_play_callback_kwargs: dict = None
    ) -> None:
        super().__init__(client, channel)

        self.timeout = timeout
        if on_play_callback is None:
            on_play_callback = self._default_on_play_callback
        if on_play_callback_kwargs is None:
            on_play_callback_kwargs = {}
        self.on_play_callback = on_play_callback
        self.on_play_kwargs = on_play_callback_kwargs

        self.queue = AudioQueue(20)
        self._next = asyncio.Event()
        self._loop = False
        self._current_audio: AudioSource = None

        self.audio_player_task = self.client.loop.create_task(self.audio_player())

    async def audio_player(self):
        while True:
            self._next.clear()
            if not self._loop:
                # Try to get the next song within 3 minutes.
                # If no song is added to the queue in time, the player will disconnect due to performance reasons.
                try:
                    async with timeout(self.timeout):
                        self._current_audio = await self.queue.get()
                except asyncio.TimeoutError:
                    self.client.loop.create_task(self.disconnect())
                    return

            # TODO: check and understand this volume part
            # self.current_audio.volume = self.volume
            self.play(self._current_audio, after=self.play_next)
            await self.on_play_callback(**self.on_play_kwargs)
            await self._next.wait()

    def play_next(self, error=None):
        if error:
            raise ce.VoiceError(str(error))
        self._next.set()

    def skip(self):
        if self.is_playing():
            # Stopping the current audio will trigger the play_next method and start the next song if any available on the queue
            self.stop()

    async def disconnect(self, *, force: bool = False) -> None:
        # TODO: check what happens if the queue if not cleared before disconnecting
        self.queue.clear()
        return await super().disconnect(force=force)

    async def _default_on_play_callback(self, **kwargs):
        # TODO add args too (not only kwargs)
        return

    def __del__(self):
        self.audio_player_task.cancel()


class AudioSource(discord.PCMVolumeTransformer):
    def __init__(self, original: discord.FFmpegPCMAudio, volume: float, *, source_data: dict = None):
        super().__init__(original, volume)
        # Metadata about the audio
        # TODO: review this data and keep only the necessary
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
    # TODO: test the maxsize
    def _init(self, maxsize) -> None:
        self._queue: t.Deque[AudioSource] = collections.deque()
               
    ### ATTENTION BELOW ###
    # Carefully overwriting this method to use async _put
    async def put(self, item):
        """Put an item into the queue.

        Put an item into the queue. If the queue is full, wait until a free
        slot is available before adding item.
        """
        while self.full():
            putter = self._get_loop().create_future()
            self._putters.append(putter)
            try:
                await putter
            except:
                putter.cancel()  # Just in case putter is not done yet.
                try:
                    # Clean self._putters from canceled putters.
                    self._putters.remove(putter)
                except ValueError:
                    # The putter could be removed from self._putters by a
                    # previous get_nowait call.
                    pass
                if not self.full() and not putter.cancelled():
                    # We were woken up by get_nowait(), but can't take
                    # the call.  Wake up the next in line.
                    self._wakeup_next(self._putters)
                raise
        return await self.put_nowait(item)

    async def put_nowait(self, item):
        """Put an item into the queue without blocking.

        If no free slot is immediately available, raise QueueFull.
        """
        if self.full():
            raise QueueFull
        await self._put(item)
        self._unfinished_tasks += 1
        self._finished.clear()
        self._wakeup_next(self._getters)
    ### ATTENTION ABOVE ###

    async def _put(self, item: AudioSource | tuple[commands.Context, str]) -> None:
        if isinstance(item, AudioSource):
            self._queue.append(item)
            return
        if isinstance(item, tuple) and isinstance(item[0], commands.Context) and isinstance(item[1], str):
            source = await AudioSource.create_source(item[0], item[1])
            self._queue.append(source)
            return
        raise TypeError(f'Cannot store type {type(item)} in this queue')

    def clear(self) -> None:
        self._queue.clear()

    def shuffle(self) -> None:
        random.shuffle(self._queue)

    def remove(self, index: int) -> None:
        if 0 <= index < len(self._queue):
            del self._queue[index]
        else:
            raise IndexError("Index out of range")

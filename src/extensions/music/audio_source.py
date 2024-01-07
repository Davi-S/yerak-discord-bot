import asyncio
import functools
from pathlib import Path

import discord
# import youtube_dl
import yt_dlp as youtube_dl
from discord.ext import commands

import custom_errors as ce

THIS_FOLDER = Path(__file__).parent
FFMPEG_PATH = THIS_FOLDER/'ffmpeg.exe'

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

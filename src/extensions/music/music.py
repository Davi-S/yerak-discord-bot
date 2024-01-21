import logging
import typing as t
from pathlib import Path

import discord
from discord.ext import commands

import bot_yerak as by
import custom_context as cc
import custom_errors as ce
import custom_voice_client as cvc
import extensions as exts

logger = logging.getLogger(__name__)

THIS_FOLDER = Path(__file__).parent
FFMPEG_PATH = THIS_FOLDER/'ffmpeg.exe'

_commands_attributes = exts.read_commands_attributes(THIS_FOLDER/'commands_attr.json')  # Global cache for config data
get_command_attributes = exts.get_command_attributes_builder(_commands_attributes)
get_command_parameters = exts.get_command_parameters_builder(_commands_attributes)


# CHECKS
def ensure_author_voice() -> t.Callable[[cc.CustomContext], bool]:
    def predicate(ctx: cc.CustomContext):
        if ctx.author.voice and ctx.author.voice.channel:
            return True
        raise ce.NoVoiceChannelError('Author is not in a voice channel')
    return commands.check(predicate)


def ensure_bot_voice() -> t.Callable[[cc.CustomContext], bool]:
    def predicate(ctx: cc.CustomContext):
        if ctx.voice_client:
            return True
        raise ce.NoVoiceChannelError('The bot is not connected to any voice channel')
    return commands.check(predicate)


def ensure_bot_playing() -> t.Callable[[cc.CustomContext], bool]:
    def predicate(ctx: cc.CustomContext):
        voice = ctx.voice_client
        return voice and voice.is_playing()
    return commands.check(predicate)


def ensure_bot_paused() -> t.Callable[[cc.CustomContext], bool]:
    def predicate(ctx: cc.CustomContext):
        voice = ctx.voice_client
        return voice and ctx.voice_client.is_paused()
    return commands.check(predicate)


# TODO: there is a logging error some times
# TODO: COMMANDS
# ☑ enter
# ☑ leave
# ☑ play/enqueue
# add_playlist
# ☑ pause
# ☑ resume
# ☑ stop
# ☑ skip
# ☑ volume
# goto
# lyrics
# ☑ loop
# ☑ now_playing
# queue
# ☑ clear
# shuffle
# delete

class Music(commands.GroupCog):
    """Play songs on a voice channel"""

    def __init__(self, bot: by.BotYerak) -> None:
        self.bot = bot

    @commands.hybrid_command(**get_command_attributes('join'))
    @ensure_author_voice()
    async def join(self, ctx: cc.CustomContext) -> None:
        destination = ctx.author.voice.channel
        if ctx.voice_client is None:
            # Attention to the custom class in the connect function.
            # This class is now the type of ctx.voice_client
            await destination.connect(cls=cvc.CustomVoiceClient)
        else:
            await ctx.voice_client.move_to(destination)
        await ctx.reply(f'Joined channel {destination.name}')
    
    @join.error
    async def on_join_error(self, ctx: cc.CustomContext, error: discord.DiscordException) -> None:
        if isinstance(error, ce.NoVoiceChannelError):
            await ctx.reply('You must be in a voice channel for the bot to join in')
        else:
            raise error

    @commands.hybrid_command(**get_command_attributes('leave'))
    @ensure_bot_voice()
    async def leave(self, ctx: cc.CustomContext) -> None:
        channel_name = ctx.voice_client.channel.name
        ctx.voice_client.queue.clear()
        await ctx.voice_client.disconnect()
        await ctx.reply(f'Disconnected from {channel_name}')
    
    @leave.error
    async def on_leave_error(self, ctx: cc.CustomContext, error: discord.DiscordException) -> None:
        if isinstance(error, ce.NoVoiceChannelError):
            await ctx.reply('The bot is not connected to any voice channel')
        else:
            raise error

    @commands.hybrid_command(**get_command_attributes('play'))
    @ensure_bot_voice()
    async def play(self, ctx: cc.CustomContext, *,
        search: str = commands.parameter(**get_command_parameters('play', 'search'))
    ) -> None:
        async with ctx.typing():
            # Put the audio in the queue. If this is the only audio in the queue, it will start automatically
            await ctx.voice_client.queue.put((ctx, search))
        # TODO: get the audio that was just added to show its title
        await ctx.reply(f'Enqueued {search}')
        
    @play.error
    async def on_play_error(self, ctx: cc.CustomContext, error: discord.DiscordException) -> None:
        # sourcery skip: remove-unnecessary-else, swap-if-else-branches
        if isinstance(error, ce.NoVoiceChannelError):
            # Try to invoke a join command and invoke the play command again
            # Not using "ctx.invoke" because it bypasses the checks and errors handlers
            join_message = ctx.message
            join_message.content = f'{(await self.bot.get_prefix(join_message))[0]}join'
            join_context = await self.bot.get_context(join_message)
            await self.bot.invoke(join_context)
            if join_context.command_failed:
                # If the join command could not be invoked successfully, just ignore.
                # The error handler of the join command will take care of it
                return
            else:
                # Try to invoke the command again.
                await self.bot.invoke(ctx)
        else:
            raise error

    @commands.hybrid_command(**get_command_attributes('pause'))
    @ensure_bot_playing()
    async def pause(self, ctx: cc.CustomContext) -> None:
        ctx.voice_client.pause()
        await ctx.reply('Paused')
        
    @pause.error
    async def on_pause_error(self, ctx: cc.CustomContext, error: discord.DiscordException) -> None:
        if isinstance(error, commands.CheckFailure):
            await ctx.reply('The bot is not playing anything')
        else:
            raise error

    @commands.hybrid_command(**get_command_attributes('resume'))
    @ensure_bot_paused()
    async def resume(self, ctx: cc.CustomContext) -> None:
        ctx.voice_client.resume()
        await ctx.reply('Resumed')

    @resume.error
    async def on_resume_error(self, ctx: cc.CustomContext, error: discord.DiscordException) -> None:
        if isinstance(error, commands.CheckFailure):
            await ctx.reply('The bot is not paused')
        else:
            raise error
    
    @commands.hybrid_command(**get_command_attributes('stop'))
    @ensure_bot_playing()
    async def stop(self, ctx: cc.CustomContext) -> None:
        ctx.voice_client.queue.clear()
        ctx.voice_client.stop()
        await ctx.reply('Queue cleared and music stopped')
    
    @stop.error
    async def on_stop_error(self, ctx: cc.CustomContext, error: discord.DiscordException) -> None:
        if isinstance(error, commands.CheckFailure):
            await ctx.reply('The bot is not playing anything')
        else:
            raise error
        
    @commands.hybrid_command(**get_command_attributes('skip'))
    @ensure_bot_playing()
    async def skip(self, ctx: cc.CustomContext) -> None:
        # Stopping the current song will trigger the "custom_voice_client.play_next" method, and play the next audio
        ctx.voice_client.stop()
        await ctx.reply('Skipped current music')
        
    @skip.error
    async def on_skip_error(self, ctx: cc.CustomContext, error: discord.DiscordException) -> None:
        if isinstance(error, commands.CheckFailure):
            await ctx.reply('The bot is not playing anything')
        else:
            raise error
        
    @commands.hybrid_command(**get_command_attributes('volume'))
    @ensure_bot_playing()
    async def volume(self, ctx: cc.CustomContext,
        volume: int = commands.parameter(**get_command_parameters('volume', 'volume'))
    ) -> None:
        volume = (max(0, min(volume, 100)))
        ctx.voice_client.volume = volume / 100
        await ctx.reply(f'Volume set to {volume}')
        
    @volume.error
    async def on_volume_error(self, ctx: cc.CustomContext, error: discord.DiscordException) -> None:
        # sourcery skip: remove-unnecessary-else, swap-if-else-branches
        if isinstance(error, commands.CheckFailure):
            await ctx.reply('The bot is not playing anything')
            return
        if isinstance(error, commands.BadArgument):
            await ctx.reply('The volume but be an integer number')
            return
        else:
            raise error
        
    @commands.hybrid_command(**get_command_attributes('loop'))
    @ensure_bot_playing()
    async def loop(self, ctx: cc.CustomContext,
        value: bool | None = commands.parameter(default=None, **get_command_parameters('loop', 'value'))
    ) -> None:
        ctx.voice_client.looping = not ctx.voice_client.looping if value is None else value
        await ctx.reply(f'The audio loop is turned {"on" if ctx.voice_client.looping else "off"}')
        
    @loop.error
    async def on_loop_error(self, ctx: cc.CustomContext, error: discord.DiscordException) -> None:
        # sourcery skip: remove-unnecessary-else, swap-if-else-branches
        if isinstance(error, commands.CheckFailure):
            await ctx.reply('The bot is not playing anything')
            return
        else:
            raise error
        
    @commands.hybrid_command(**get_command_attributes('clear'))
    async def clear(self, ctx: cc.CustomContext) -> None:
        ctx.voice_client.queue.clear() 
        await ctx.reply('Queue cleared')
        
    @commands.hybrid_command(**get_command_attributes('now_playing'))
    @ensure_bot_playing()
    async def now_playing(self, ctx: cc.CustomContext) -> None:
        embed = self.create_embed(ctx.voice_client.current_audio)
        await ctx.reply(embed=embed)
        
    @now_playing.error
    async def on_now_playing_error(self, ctx: cc.CustomContext, error: discord.DiscordException) -> None:
        # sourcery skip: remove-unnecessary-else, swap-if-else-branches
        if isinstance(error, commands.CheckFailure):
            await ctx.reply('The bot is not playing anything')
            return
        else:
            raise error
         
    def create_embed(self, audio: cvc.AudioSource):
        # TODO: make better embed
        return (
            discord.Embed(
                title='Now playing',
                description=f'```\n{audio.title}\n```',
                color=0x175639,
            )
            .add_field(name='Duration', value=audio.duration, inline=False)
            .add_field(name='Requested by', value=audio.requester.mention, inline=False)
            .add_field(
                name='Uploader',
                value=f'[{audio.uploader}]({audio.uploader_url})',
                inline=False
            )
            .add_field(name='URL', value=f'[Click]({audio.url})'.format(self), inline=False)
            .set_thumbnail(url=audio.thumbnail)
        )

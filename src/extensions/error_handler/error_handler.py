import contextlib
import logging

import discord
from discord.ext import commands

import bot_yerak as by
import custom_context as cc
import custom_errors as ce
from settings import settings

logger = logging.getLogger(__name__)


class ErrorHandler(commands.Cog):
    """Global error handler class"""

    handle_error_method_name = '_handle_{error_name}'

    def __init__(self, bot: by.BotYerak) -> None:
        self.bot = bot
        self.ignored_errors = ()

    @commands.Cog.listener()
    async def on_command_error(self, ctx: cc.CustomContext, error: commands.CommandError):
        # This prevents any commands with local handlers from being handled here
        if hasattr(ctx.command, 'on_error'):
            return

        # This prevents any cogs with an overwritten cog_command_error from being handled here
        if cog := ctx.cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        # Check for original exceptions raised and sent to CommandInvokeError
        # If nothing is found. We keep the exception passed to this method
        error = getattr(error, 'original', error)

        # Ignore errors if needed
        if isinstance(error, self.ignored_errors):
            return

        if not hasattr(
            self,
            self.handle_error_method_name.format(error_name=error.__class__.__name__)
        ):
            return await self._unhandled_error(ctx, error)
        
        method = getattr(
            self,
            self.handle_error_method_name.format(error_name=error.__class__.__name__)
        )
        return await method(ctx, error)

    async def _unhandled_error(self, ctx: cc.CustomContext, error: commands.CommandError) -> None:        
        # Warn developers
        error_message = {
            'Error Class Name': error.__class__.__name__,
            'Error Message': str(error),
            'Message': ctx.message.content,
            'Guild/Channel': f'Guild: {ctx.guild.name} -> {ctx.guild.id}' if ctx.guild else f'channel: {ctx.channel.name} -> {ctx.channel.id}' if ctx.channel else 'None',
            'User': f'{ctx.author.name} -> {ctx.author.id}',
            'Cog': ctx.command.cog.qualified_name if ctx.command and ctx.command.cog else 'None',
        }
        embed = discord.Embed(title='Unhandled Exception')
        for key, value in error_message.items():
            embed.add_field(name=key, value=value, inline=False)
        for developer_id in settings.users_developers_ids:
            if user := await self.bot.fetch_user(int(developer_id)):
                with contextlib.suppress(discord.errors.Forbidden):
                    await user.send(embed=embed)
                    
        # Log the error
        # Using try except to log error with traceback (logger.exception)
        try:
            raise ce.UnhandledError()
        except ce.UnhandledError:
            logger.exception(f'Unhandled Error: {error}')

    async def _handle_NotAuthorizedUser(self, ctx: cc.CustomContext, error: commands.CommandError) -> None:
        logger.warning(f'User "{ctx.author.name}" with id "{ctx.author.id}" tried to use the command "{ctx.command.name}"')
        with contextlib.suppress(Exception):
            # Try to send DM message to the author
            await ctx.message.author.send(f'You cannot use the command `{ctx.command.qualified_name}`')
        await ctx.reply('You cannot use this command')

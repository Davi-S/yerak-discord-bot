import colorsys
import itertools
import logging
import random
from pathlib import Path

import discord
from discord.ext import commands, tasks

from bot_yerak import BotYerak

from .. import get_command_attributes_builder, read_commands_attributes

logger = logging.getLogger(__name__)

THIS_FOLDER = Path(__file__).parent


_commands_attributes = read_commands_attributes(THIS_FOLDER/'commands_attr.json')  # Global cache for config data
get_command_attributes = get_command_attributes_builder(_commands_attributes)


class MemberListConverter(commands.Converter):
    async def convert(self, ctx, argument):
        members = []
        for mention in argument.split(' '):
            try:
                member = await commands.MemberConverter().convert(ctx, mention)
                members.append(member)
            except commands.errors.BadArgument:
                # Ignore if the mention is not a valid member
                pass  
        return members

class Rave(commands.GroupCog):
    """Light up the server"""
    long_description = (
    """Create top hierarchy roles and change their color dynamically, making the server very animated.
    Every rave has a 10 minutes timeout"""
    )
    # TODO: do not let two raves at the same time
    # TODO: check how the rave behaves in different guilds
    def __init__(self, bot: BotYerak) -> None:
        self.bot = bot
        self.role_name = "Yerak's Raver"
        self.timeout = 600  # 600 seconds equals to 10 minutes
        self.tasks = self.get_tasks()
        self.setup_tasks_error_handler()

    @commands.hybrid_command(**get_command_attributes('pause'))
    async def pause(self, ctx: commands.Context) -> None:
        self.stop_tasks()
        await ctx.reply('Rave paused')

    @commands.hybrid_command(**get_command_attributes('stop'))
    async def stop(self, ctx: commands.Context) -> None:
        self.stop_tasks()
        await self.delete_roles(ctx, all=True)
        await ctx.reply('Rave stopped')

    @commands.hybrid_command(**get_command_attributes('hue_cycle'))
    async def hue_cycle(self, ctx: commands.Context,
        step: float = commands.parameter(default=0.01, description='How much the color will change each time. Goes from 0 to 1'),
        speed: float = commands.parameter(default=1.0, description='The time between each color change in seconds'),
        *,
        members: list[discord.Member] | None = commands.parameter(converter=MemberListConverter, default=None, description='The members that will receive the rave role. Default is everyone that can')
    ) -> None:
        # Prepare roles
        roles = await self.get_roles(ctx, 1)
        await self.apply_all_roles(roles, members or ctx.guild.members)
        # Prepare task
        self.hue_cycle_task.change_interval(seconds=speed)
        self.hue_cycle_task.count = self.timeout // speed
        self.hue_cycle_task.start(ctx, roles[0].id, step)
        await ctx.reply('Hue Cycle rave started')

    @tasks.loop(seconds=1)
    async def hue_cycle_task(self, ctx: commands.Context, role_id: int, step: float = 0.01):
        # get the role every time to get the latest color
        role = ctx.guild.get_role(role_id)
        role_color_hsv = colorsys.rgb_to_hsv(*[component / 255.0 for component in role.color.to_rgb()])
        # Check if the role has no initial color and give some arbitrary HSV color
        if role_color_hsv == (0, 0, 0):
            role_color_hsv = (0.5, 0.8, 0.8)
        # increment the hue cycling to the beginning if it gets to the max value
        new_color = ((role_color_hsv[0] + step) % 1.0, role_color_hsv[1], role_color_hsv[2])
        await role.edit(color=discord.Color.from_hsv(*new_color))
            
    @commands.hybrid_command(**get_command_attributes('crazy'))
    async def crazy(self, ctx: commands.Context,
        amount: int = commands.parameter(default=3, description='How much different colors at the same time'),
        speed: float = commands.parameter(default=4.0, description='The time between each color change in seconds'),
        *,
        members: list[discord.Member] | None = commands.parameter(converter=MemberListConverter, default=None, description='The members that will receive the rave role. Default is everyone that can')
    ) -> None:
        # Prepare roles
        roles = await self.get_roles(ctx, amount)
        await self.apply_even_roles(roles, members or ctx.guild.members)
        # Prepare tasks
        self.crazy_task.change_interval(seconds=speed)
        self.crazy_task.count = self.timeout // speed
        self.crazy_task.start(roles)
        await ctx.reply('Crazy rave started')
        
    @tasks.loop(seconds=4)
    async def crazy_task(self, roles: list[discord.Role]):
        for role in roles:
            color_hsv = (random.random(), 0.8, 0.8)
            await role.edit(color=discord.Color.from_hsv(*color_hsv))
            
    async def create_roles(self, ctx: commands.Context, amount: int) -> list[discord.Role]:
        # Create new roles
        created_roles = []
        for _ in range(amount):
            role: discord.Role = await ctx.guild.create_role(name=self.role_name)
            created_roles.append(role)

        # Sort roles and update their positions
        roles_positions = {}
        for idx, role in enumerate(ctx.guild.roles):
            roles_positions[role] = idx
        roles_positions = dict(reversed(list(roles_positions.items())))
        found = False
        for role, position in roles_positions.items():
            if role.name == self.bot.user.name:
                found = True
                for idx, created_role in enumerate(created_roles, start=1):
                    roles_positions[created_role] = position - idx
            elif self.is_rave_role(role):
                break
            elif found:
                roles_positions[role] = position - amount
        roles_positions = dict(sorted(roles_positions.items(), key=lambda x: x[1]))
        await ctx.guild.edit_role_positions(positions=roles_positions)
        return created_roles

    async def delete_roles(self, ctx: commands.Context, amount: int = 1, all=False) -> None:
        deleted = 0
        for role in ctx.guild.roles:
            if self.is_rave_role(role) and ((deleted < amount) or (all)):
                await role.delete()
                deleted += 1

    async def get_roles(self, ctx: commands.Context, amount: int) -> list[discord.Role]:
        existing_roles = [role for role in ctx.guild.roles if self.is_rave_role(role)]
        if (existing_roles_amount := len(existing_roles)) < amount:
            existing_roles.extend(await self.create_roles(ctx, amount-existing_roles_amount))
        return existing_roles[:amount]

    async def apply_all_roles(self, roles: list[discord.Role], members: list[discord.Member]) -> None:
        for member in members:
            await member.add_roles(*roles)
            
    async def apply_even_roles(self, roles: list[discord.Role], members: list[discord.Member]) -> None:
        roles_cycle = itertools.cycle(roles)
        for member in members:
            await member.add_roles(next(roles_cycle))

    def is_rave_role(self, role: discord.Role) -> bool:
        return role.name == self.role_name

    def get_tasks(self) -> tuple[tasks.Loop]:
        tasks_list = []
        for attr in dir(self):
            if attr.endswith('_task'):
                task = getattr(self, attr)
                if isinstance(task, tasks.Loop):
                    tasks_list.append(task)
        return tuple(tasks_list)

    def stop_tasks(self) -> None:
        for task in self.tasks:
            if task.is_running():
                task.stop()
    
    def cog_unload(self):
        self.stop_tasks()
    
    async def on_tasks_error(self, _, error: discord.DiscordException):
        # Because this function is not being set by a decorator, it receives two "self" arguments when called. Using the "_" to ignore the second "self" argument
        # In case the role is deleted while the task is running
        if isinstance(error, (AttributeError, discord.errors.NotFound)):
            pass
        else:
            logger.error(f'Error on a task: {error}')
    
    def setup_tasks_error_handler(self):
        for task in self.tasks:
            task.error(self.on_tasks_error)
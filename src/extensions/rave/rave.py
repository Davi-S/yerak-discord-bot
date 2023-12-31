import colorsys
import logging
from pathlib import Path

import discord
from discord.ext import commands, tasks

from bot_yerak import BotYerak

from .. import get_command_attributes_builder, read_commands_attributes

logger = logging.getLogger(__name__)

THIS_FOLDER = Path(__file__).parent


_commands_attributes = read_commands_attributes(THIS_FOLDER/'commands_attr.json')  # Global cache for config data
get_command_attributes = get_command_attributes_builder(_commands_attributes)


class Rave(commands.GroupCog):
    """Light up the server"""
    # TODO: do not let two raves at the same time
    # TODO: stop all raves and delete roles before exiting of unloading the cog

    def __init__(self, bot: BotYerak) -> None:
        self.bot = bot
        self.role_name = "Yerak's Raver"

    async def create_roles(self, ctx: commands.Context, amount: int):
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

            elif role.name == self.role_name:
                break
            elif found:
                roles_positions[role] = position - amount
        roles_positions = dict(
            sorted(roles_positions.items(), key=lambda x: x[1]))

        await ctx.guild.edit_role_positions(positions=roles_positions)

        return created_roles

    async def delete_roles(self, ctx: commands.Context, amount: int = 1, all=False):
        deleted = 0
        for role in ctx.guild.roles:
            if role.name == self.role_name and ((deleted < amount) or (all)):
                await role.delete()
                deleted += 1

    @commands.hybrid_command(**get_command_attributes('create'))
    async def create(self, ctx: commands.Context) -> None:
        await self.create_roles(ctx, 6)

    @commands.hybrid_command(**get_command_attributes('delete'))
    async def delete(self, ctx: commands.Context) -> None:
        await self.delete_roles(ctx, all=True)

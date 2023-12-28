import discord
from discord.ext import commands


class MyHelp(commands.HelpCommand):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.no_category_qualified_name = 'Other'
        self.no_category_description = 'Other commands'

        kwargs['command_attrs'] = {
            "help": "Display information about available categories, commands and other useful information",
            "brief": "Show a help message",
        }

    async def send_bot_help(self, mapping: dict[commands.Cog | None, list[commands.Command]]) -> None:
        categories = []

        for cog, commands_list in mapping.items():
            if commands_count := len(await self.filter_commands(commands_list)):
                category_name = cog.qualified_name if cog else self.no_category_qualified_name
                if category_name == self.cog.qualified_name:
                    continue
                category_description = cog.description if cog else self.no_category_description
                categories.append((category_name, category_description, commands_count))

        categories = sorted(categories, key=lambda x: x[0])

        embed = discord.Embed()
        embed.title = self.embed_title()
        embed.description = (
            f'Use `<prefix>{self.invoked_with} [category]` for more info on a category.\n'
            f'You can also use `<prefix>{self.invoked_with} [command]` for more info on a command.'
        )
        embed.add_field(
            name=f'Total of {len(categories)} categories and {sum(category[2] for category in categories)} commands',
            value='\n'.join(f'{category[0]} ({category[2]}) - {category[1]}' for category in categories),
            inline=False
        )
        embed.set_footer(text=self.embed_footer())
        await self.send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog) -> None:
        if cog:
            available_commands = await self.filter_commands(cog.get_commands())
        else:
            available_commands = self.get_bot_mapping()[None]

        embed = discord.Embed()
        embed.title = self.embed_title(
            cog.qualified_name if cog else self.no_category_qualified_name)
        embed.description = (
            f'Use `<prefix>{self.invoked_with} [command]` for more info on a command.\n'
            f'You can also use `<prefix>{self.invoked_with}` for more info on all categories.'
        )
        embed.add_field(
            name=f'Total of {len(available_commands)} commands',
            value='\n'.join(
                f'`{command.qualified_name}`: {command.short_doc}' for command in available_commands),
            inline=False
        )
        embed.set_footer(text=self.embed_footer())
        await self.send(embed=embed)

    async def send_command_help(self, command: commands.Command) -> None:
        embed = discord.Embed()
        embed.title = self.embed_title(command.qualified_name)
        embed.description = (
            f'Use `<prefix>{self.invoked_with}` for more info on all categories.\n'
            f'You can also use `<prefix>{self.invoked_with} [category]` for more info on a category.'
        )
        embed.add_field(
            name='Command Information',
            value='\n'.join(f'{key}: {value}' for key,
                            value in self.get_command_attributes(command).items()),
            inline=False
        )
        embed.set_footer(text=self.embed_footer())
        await self.send(embed=embed)

    async def send_error_message(self, error: str) -> None:
        if error == self.no_category_qualified_name:
            return

        embed = discord.Embed()
        embed.title = self.embed_title()
        embed.description = (
            f'Use `<prefix>{self.invoked_with}` for more info on all categories.\n'
            f'You can also use `<prefix>{self.invoked_with} [category]` for more info on a category.'
        )
        embed.add_field(name='**Error**', value=error, inline=False)
        embed.set_footer(text=self.embed_footer())
        await self.send(embed=embed)

    async def command_not_found(self, string: str) -> None:
        if string == self.no_category_qualified_name:
            await self.send_cog_help(None)
            return 'Other'
        return super().command_not_found(string)

    async def send(self, *args, **kwargs) -> None:
        await self.context.message.reply(*args, **kwargs)

    def prefixes(self) -> list:
        prefixes = self.context.bot.command_prefix(
            self.context.bot, self.context.message)[1:]
        prefixes[0] = f'@{self.context.bot.get_user(int(prefixes[0][3:-2])).name} '
        return prefixes

    def embed_footer(self) -> str:
        return (
            '<> is a required parameter, [] is an optional parameter.\n'
            f'Other prefixes are: {" ".join(f"[{prefix}]" for prefix in self.prefixes())}'
        )

    def embed_title(self, topic: str = '') -> str:
        return 'Yerak\'s help' if not topic else f'Yerak\'s help on "{topic}"'

    def get_command_attributes(self, command: commands.Command) -> dict:
        return {
            'Description': command.help,
            'Usage': f'<prefix>{command.name} {command.signature}',
            'Aliases': ', '.join(command.aliases) or 'No aliases',
            'Category': self.no_category_qualified_name if not command.cog else command.cog.qualified_name,
        }

import discord
from discord.ext import commands

# TODO: fix these embeds

class MyHelp(commands.HelpCommand):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.no_category_qualified_name = 'Other'
        self.no_category_description = 'Other commands'
        self.color_hex = 0x175639
        kwargs['command_attrs'] = {
            "help": "Display information about available categories, commands and other useful information",
            "brief": "Show a help message",
        }

    async def send_bot_help(self, mapping: dict[commands.Cog | None, list[commands.Command]]) -> None:
        # Get categories (cogs)
        categories = []
        for cog, commands_list in mapping.items():
            if commands_count := len(await self.filter_commands(commands_list)):
                category_name = cog.qualified_name if cog else self.no_category_qualified_name
                category_description = cog.description if cog else self.no_category_description
                categories.append((category_name, category_description, commands_count))
        categories = sorted(categories, key=lambda x: x[0])

        # Create embed
        embed = self.get_embed()
        embed.title = self.embed_title()
        embed.description = (f'Total of **{len(categories)}** categories and **{sum(category[2] for category in categories)}** commands')
        for category in categories:
            embed.add_field(
                name=f'{category[0]} ({category[2]})',
                value=category[1],
                inline=False
            )
        embed.set_footer(text=self.embed_footer(full=False))
        await self.send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog) -> None:
        if cog:
            available_commands = await self.filter_commands(cog.get_commands())
        else:
            available_commands = self.get_bot_mapping()[None]
        cog_name = cog.qualified_name if cog else self.no_category_qualified_name
        
        embed = self.get_embed()
        embed.title = self.embed_title(cog_name) + ' category'
        embed.description = (f'Total of **{len(available_commands)}** commands in this category')
        for command in available_commands:
            embed.add_field(
                name=command.qualified_name,
                value=command.short_doc,
                inline=False
            )
        embed.set_footer(text=self.embed_footer(full=False))
        await self.send(embed=embed)

    async def send_command_help(self, command: commands.Command) -> None:
        embed = self.get_embed()
        embed.title = self.embed_title(command.qualified_name) + ' command'
        embed.description = command.help
        # TODO: add command parameters field
        for key, value in self.get_command_attributes(command).items():
            embed.add_field(
                name=key,
                value=value,
                inline=False
            )
        embed.set_footer(text=self.embed_footer())
        await self.send(embed=embed)

    async def send_error_message(self, error: str) -> None:
        # See the "command_not_found" method
        # This prevents an error when the users tries to get help for the "no cog" cog
        if error == self.no_category_qualified_name:
            return

        embed = self.get_embed()
        embed.title = self.embed_title()
        embed.description = f'**Error**\n{error}\n\nRemember that commands and categories names are case sensitive'
        embed.set_footer(text=self.embed_footer(full=False))
        await self.send(embed=embed)

    async def command_not_found(self, string: str) -> None:
        if string == self.no_category_qualified_name:
            await self.send_cog_help(None)
            return self.no_category_qualified_name
        return super().command_not_found(string)
    
    # OWN METHODS BELLOW #
    async def send(self, *args, **kwargs) -> None:
        await self.context.message.reply(*args, **kwargs)

    def prefixes(self) -> list[str]:
        prefixes = self.context.bot.command_prefix(self.context.bot, self.context.message)[1:]
        prefixes[0] = f'@{self.context.bot.get_user(int(prefixes[0][3:-2])).name} '
        return prefixes

    def get_embed(self):
        return discord.Embed(color=self.color_hex) 
    
    def embed_title(self, topic: str = '') -> str:
        return 'Yerak\'s help' if not topic else f'Yerak\'s help on "{topic}"'

    def embed_footer(self, full=True) -> str:
        first = '<> is a required parameter, [] is an optional parameter.\n'
        second = f'Other prefixes are: {" ".join(f"[{prefix}]" for prefix in self.prefixes())}'
        return first + second if full else second

    def get_command_attributes(self, command: commands.Command) -> dict:
        return {
            'Usage': f'<prefix>{command.name} {command.signature}',
            'Aliases': ', '.join(command.aliases) or 'No aliases',
            'Category': self.no_category_qualified_name if not command.cog else command.cog.qualified_name,
        }

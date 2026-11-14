import inspect

import discord
from discord.ext import commands


class DocstringHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__(
            command_attrs={
                "help": "Shows help documentation for commands.",
                "aliases": ["h"],
            }
        )

    # 1. Triggered on `!help` -> List all commands alphabetically without cog headers
    async def send_bot_help(self, mapping):
        # Gather all commands from all cogs into a single flat list
        all_commands: list[commands.Command] = []
        for command_list in mapping.values():
            all_commands.extend(command_list)

        # Filter out hidden commands and commands the user cannot run
        filtered_commands = await self.filter_commands(all_commands, sort=True)

        if not filtered_commands:
            await self.get_destination().send("No commands available.")
            return

        lines: list[str] = []
        for cmd in filtered_commands:
            full_doc = cmd.help or ""
            # Extract first non-empty line of the docstring
            first_line = (
                full_doc.strip().split("\n")[0]
                if full_doc
                else "No description provided."
            )
            lines.append(f"`{cmd.name}` — {first_line}")

        embed = discord.Embed(
            title="Commands",
            description="\n".join(lines),
            color=discord.Color.blurple(),
        )
        embed.set_footer(text="Type help <command> for detailed usage.")

        channel = self.get_destination()
        await channel.send(embed=embed)

    # 2. Triggered on `!help <command>` -> Shows full docstring
    async def send_command_help(self, command: commands.Command):
        embed = discord.Embed(
            title=f"Command: {command.name}",
            color=discord.Color.green(),
        )

        full_doc = (
            inspect.cleandoc(command.help)
            if command.help
            else "No description available."
        )
        embed.description = full_doc

        syntax = f"`{command.name} {command.signature}`".strip()
        embed.add_field(name="Syntax", value=syntax, inline=False)

        if command.aliases:
            embed.add_field(
                name="Aliases",
                value=", ".join(f"`{alias}`" for alias in command.aliases),
                inline=False,
            )

        channel = self.get_destination()
        await channel.send(embed=embed)

    # 3. Triggered when an unknown command is requested
    async def send_error_message(self, error: str):
        embed = discord.Embed(
            title="Help Error",
            description=error,
            color=discord.Color.red(),
        )
        channel = self.get_destination()
        await channel.send(embed=embed)

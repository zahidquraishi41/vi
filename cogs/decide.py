import random
import re

from discord.ext import commands

from main import ViBot


class Decide(commands.Cog):
    def __init__(self, bot: ViBot):
        self.bot = bot
        self.delimiter_pattern = re.compile(r",\s*or\s+|\s+or\s+|,", re.IGNORECASE)
        self.choices = (
            "I go with",
            "Let's go with",
            "My pick is",
            "Definitely",
            "I'd choose",
        )

    @commands.command(aliases=["pick", "choose"])
    async def decide(self, ctx: commands.Context, *, options: str | None = None):
        """Picks a random choice from a list of options.
        Usage:
            decide red or black
        Output:
            Definitely red"""
        if not options:
            return await self.bot.send_french(
                ctx, "I need at least two distinct options to decide!"
            )

        # Split on commas and 'or', clean whitespace, and drop empty choices
        raw_choices = self.delimiter_pattern.split(options)
        choices = [choice.strip() for choice in raw_choices if choice.strip()]

        if len(choices) < 2:
            return await self.bot.send_french(
                ctx, "I need at least two distinct options to decide!"
            )

        picked = random.choice(choices)
        prefix = random.choice(self.choices)
        await self.bot.send_french(ctx, f"{prefix} {picked}")


async def setup(bot: ViBot) -> None:
    await bot.add_cog(Decide(bot))

from discord.ext import commands

from main import ViBot


class Fact(commands.Cog):
    def __init__(self, bot: ViBot):
        self.bot = bot
        self.url = "https://uselessfacts.jsph.pl/random.json?language=en"

    @commands.command()
    async def fact(self, ctx: commands.Context):
        """Sends a random fact.
        Example: There are a million ants for every person on Earth."""
        try:
            response = await self.bot.fetch(self.url, "text")
            await self.bot.send_french(ctx, response)
        except Exception as err:  # noqa
            await ctx.send(str(err) or f"Unexpected error ({type(err).__name__})")


async def setup(bot: ViBot) -> None:
    await bot.add_cog(Fact(bot))

from discord.ext import commands

from main import ViBot


class Coffee(commands.Cog):
    def __init__(self, bot: ViBot):
        self.bot = bot
        self.url = "https://coffee.alexflipnote.dev/random.json"

    @commands.hybrid_command()
    async def coffee(self, ctx: commands.Context):
        """Sends a random image of coffee."""
        await ctx.defer()

        try:
            coffee = await self.bot.fetch(self.url, "file")
            await ctx.send(coffee)
        except Exception as err:  # noqa
            await ctx.send(str(err) or f"Unexpected error ({type(err).__name__})")


async def setup(bot: ViBot) -> None:
    await bot.add_cog(Coffee(bot))

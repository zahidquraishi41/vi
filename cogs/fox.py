from discord.ext import commands

from main import ViBot


class Fox(commands.Cog):
    def __init__(self, bot: ViBot):
        self.bot = bot
        self.url = "https://randomfox.ca/floof/"

    @commands.command(aliases=["floof"])
    async def fox(self, ctx: commands.Context):
        """Sends a random image of fox."""
        try:
            response = await self.bot.fetch(self.url, "image")
            await ctx.send(response)
        except Exception as err:  # noqa
            await ctx.send(str(err) or f"Unexpected error ({type(err).__name__})")


async def setup(bot: ViBot) -> None:
    await bot.add_cog(Fox(bot))

from discord.ext import commands

from main import ViBot


class Duck(commands.Cog):
    def __init__(self, bot: ViBot):
        self.bot = bot
        self.url = "https://random-d.uk/api/random"

    @commands.command(aliases=['quack'])
    async def duck(self, ctx: commands.Context):
        """Sends a random image of duck."""
        try:
            duck = await self.bot.fetch(self.url, "url")
            await ctx.send(duck)
        except Exception as err:  # noqa
            await ctx.send(str(err) or f"Unexpected error ({type(err).__name__})")


async def setup(bot: ViBot) -> None:
    await bot.add_cog(Duck(bot))

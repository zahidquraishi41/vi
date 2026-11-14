from random import randint

from discord.ext import commands

from main import ViBot


class Xkcd(commands.Cog):
    def __init__(self, bot: ViBot):
        self.bot = bot

    @property
    def url(self):
        num = randint(1, 3315)
        while num == 404:
            num = randint(1, 3315)
        return f"https://xkcd.com/{num}/info.0.json"

    @commands.command()
    async def xkcd(self, ctx: commands.Context):
        """Sends a random xkcd comic."""
        try:
            response = await self.bot.fetch(self.url, "img")
            await ctx.send(response)
        except Exception as err:  # noqa
            await ctx.send(str(err) or f"Unexpected error ({type(err).__name__})")


async def setup(bot: ViBot) -> None:
    await bot.add_cog(Xkcd(bot))

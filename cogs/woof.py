from discord.ext import commands

from main import ViBot


class Woof(commands.Cog):
    def __init__(self, bot: ViBot):
        self.bot = bot
        self.url = "https://random.dog/woof.json"

    @commands.command(aliases=['dog', 'doggy', 'doggo'])
    async def woof(self, ctx: commands.Context):
        """Sends a random picture of dog."""
        try:
            response = await self.bot.fetch(self.url, "url")
            await ctx.send(response)
        except Exception as err:  # noqa
            await ctx.send(str(err) or f"Unexpected error ({type(err).__name__})")


async def setup(bot: ViBot) -> None:
    await bot.add_cog(Woof(bot))

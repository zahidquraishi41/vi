from discord.ext import commands

from main import ViBot


class Poem(commands.Cog):
    def __init__(self, bot: ViBot):
        self.bot = bot
        self.url = "https://poetrydb.org/linecount,random/4-12;1"

    @commands.command()
    async def poem(self, ctx: commands.Context):
        """Sends a random poem of 4 to 12 lines"""
        try:
            response = await self.bot.fetch(self.url, "0")
            title = response["title"] + "  -" + response["author"]
            lines = "\n".join(response["lines"])
            await self.bot.send_french(ctx, title + "\n\n" + lines)
        except Exception as err:  # noqa
            await ctx.send(str(err) or f"Unexpected error ({type(err).__name__})")


async def setup(bot: ViBot) -> None:
    await bot.add_cog(Poem(bot))

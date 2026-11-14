from discord.ext import commands

from main import ViBot


class Quote(commands.Cog):
    def __init__(self, bot: ViBot):
        self.bot = bot
        self.url = "https://api.animechan.io/v1/quotes/random"

    @commands.command()
    async def quote(self, ctx: commands.Context):
        """Sends a random anime quote."""
        try:
            quote, anime, char = await self.bot.fetch(
                self.url, ["data.content", "data.anime.name", "data.character.name"]
            )
            await self.bot.send_french(ctx, f"{quote}  -{char} ({anime})")
        except Exception as err:  # noqa
            await ctx.send(str(err) or f"Unexpected error ({type(err).__name__})")


async def setup(bot: ViBot) -> None:
    await bot.add_cog(Quote(bot))

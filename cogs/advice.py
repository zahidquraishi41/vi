from discord.ext import commands

from main import ViBot


class Advice(commands.Cog):
    def __init__(self, bot: ViBot):
        self.bot = bot
        self.url = "https://api.adviceslip.com/advice"

    @commands.command()
    async def advice(self, ctx: commands.Context, *, user: str | None = None):
        """Sends a random piece of advice.
        Example: Don't be afraid of silly ideas."""

        try:
            response = await self.bot.fetch(self.url, "slip.advice")
            if user:
                await ctx.send(ctx.author.mention if user == "me" else user)
            await self.bot.send_french(ctx, response)
        except Exception as err:  # noqa
            await ctx.send(str(err) or f"Unexpected error ({type(err).__name__})")


async def setup(bot: ViBot) -> None:
    await bot.add_cog(Advice(bot))

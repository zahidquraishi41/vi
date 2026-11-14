from discord.ext import commands

from main import ViBot


class Insult(commands.Cog):
    def __init__(self, bot: ViBot):
        self.bot = bot
        self.url = "https://evilinsult.com/generate_insult.php?lang=en&type=json"

    @commands.command()
    async def insult(self, ctx: commands.Context, *, user: str | None = None):
        """Sends a random insult, optionally targeting a user.
        Example: You pusillanimous scoundrel."""
        try:
            response = await self.bot.fetch(self.url, "insult")
            if user:
                await ctx.send(ctx.author.mention if user == "me" else user)
            await self.bot.send_french(ctx, response)
        except Exception as err:  # noqa
            await ctx.send(str(err) or f"Unexpected error ({type(err).__name__})")


async def setup(bot: ViBot) -> None:
    await bot.add_cog(Insult(bot))

from random import choice

from discord.ext import commands

from main import ViBot


class Encourage(commands.Cog):
    def __init__(self, bot: ViBot):
        self.bot = bot

    @commands.command(aliases=["enc"])
    async def encourage(self, ctx: commands.Context, *, user: str | None = None):
        """Sends a random encouraging quote.
        Example: Success is the progressive realization of a worthy goal."""
        if choice(["zen", "aff"]) == "zen":
            quote = await self.zenquotes()
        else:
            quote = await self.affirmations()
        if user:
            await ctx.send(ctx.author.mention if user == "me" else user)
        await self.bot.send_french(ctx, quote)

    async def zenquotes(self) -> str:
        url = "https://zenquotes.io/api/random"
        try:
            msg, author = await self.bot.fetch(url, ["0.q", "0.a"])
            return msg + " -" + author
        except Exception as err:  # noqa
            return str(err)

    async def affirmations(self) -> str:
        url = "https://www.affirmations.dev/"
        try:
            return await self.bot.fetch(url, "affirmation")
        except Exception as err:  # noqa
            return str(err)


async def setup(bot: ViBot) -> None:
    await bot.add_cog(Encourage(bot))

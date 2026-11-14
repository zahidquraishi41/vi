from discord.ext import commands

from main import ViBot


class Excuse(commands.Cog):
    def __init__(self, bot: ViBot):
        self.bot = bot
        self.url = "https://excuser-three.vercel.app/v1/excuse/"
        self.categories = (
            "family",
            "office",
            "children",
            "college",
            "party",
            "funny",
            "unbelievable",
            "developers",
            "gaming",
        )

    @commands.command()
    async def excuse(self, ctx: commands.Context, category: str | None = None):
        """Sends a random excuse. optionally filtered by category.

        Categories:
            family, office, children, college, party, funny, unbelievable, developers, gaming

        Example: I drove to the previous employer yesterday."""
        if category:
            category = category.strip().lower()
            if category not in self.categories:
                return await self.bot.send_french(ctx, "Invalid category!")
        url = self.url + category if category else self.url

        try:
            response = await self.bot.fetch(url, "0.excuse")
            await self.bot.send_french(ctx, response)
        except Exception as err:  # noqa
            await ctx.send(str(err) or f"Unexpected error ({type(err).__name__})")


async def setup(bot: ViBot) -> None:
    await bot.add_cog(Excuse(bot))

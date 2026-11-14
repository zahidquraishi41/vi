from discord.ext import commands

from main import ViBot


class Rizz(commands.Cog):
    def __init__(self, bot: ViBot):
        self.bot = bot
        self.url = "https://rizzapi.vercel.app/random"

    @commands.command()
    async def rizz(self, ctx: commands.Context, *, user: str | None = None):
        """Sends a random pickup line.
        Example: Sorry, but you owe me a drink. [Why?] Because when I looked at you, I dropped mine."""
        try:
            response = await self.bot.fetch(self.url, "text")
            if user:
                if user == "me":
                    user = ctx.author.mention
                await ctx.send(user)
            await self.bot.send_french(ctx, response)
        except Exception as err:  # noqa
            await ctx.send(str(err) or f"Unexpected error ({type(err).__name__})")


async def setup(bot: ViBot) -> None:
    await bot.add_cog(Rizz(bot))

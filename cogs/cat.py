from urllib.parse import quote

from discord.ext import commands

from main import ViBot


class Cat(commands.Cog):
    def __init__(self, bot: ViBot):
        self.bot = bot
        self.url = "https://cataas.com/cat"

    @commands.hybrid_command(aliases=['car', 'meow', 'neko', 'nyaa', 'myaa'])
    async def cat(self, ctx: commands.Context, *, message: str | None = None):
        """Sends a random image of cat."""
        await ctx.defer()
        url = f"{self.url}/says/{quote(message)}" if message else self.url

        try:
            cat = await self.bot.fetch(url, "url", {"json": "true"})
            await ctx.send(cat)
        except Exception as err:  # noqa
            await ctx.send(str(err) or f"Unexpected error ({type(err).__name__})")


async def setup(bot: ViBot) -> None:
    await bot.add_cog(Cat(bot))

import random

from discord.ext import commands

from main import ViBot


class Meme(commands.Cog):
    def __init__(self, bot: ViBot):
        self.bot = bot
        self.url = "https://meme-api.com/gimme/50"
        self.meme_urls: list[str] = []

    @commands.command()
    async def meme(self, ctx: commands.Context):
        """Sends a random meme from reddit."""
        if not self.meme_urls:
            try:
                response = await self.bot.fetch(self.url, "memes")
                for meme in response:
                    if not meme["nsfw"]:
                        self.meme_urls.append(meme["url"])
            except Exception as err:  # noqa
                return await ctx.send(str(err) or f"Unexpected error ({type(err).__name__})")

        i = random.randrange(len(self.meme_urls))
        url = self.meme_urls.pop(i)
        await ctx.send(url)


async def setup(bot: ViBot) -> None:
    await bot.add_cog(Meme(bot))

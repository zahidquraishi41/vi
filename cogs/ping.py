from discord.ext import commands

from main import ViBot


class Ping(commands.Cog):
    def __init__(self, bot: ViBot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx: commands.Context):
        """Simple ping-pong latency check."""
        latency_ms = round(self.bot.latency * 1000)
        await ctx.send(f"Pong! {latency_ms}ms")


async def setup(bot: ViBot):
    await bot.add_cog(Ping(bot))

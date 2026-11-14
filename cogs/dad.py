import random
import re
from collections.abc import Awaitable, Callable

import discord
from discord.ext import commands

from main import ViBot


class Dad(commands.Cog):
    def __init__(self, bot: ViBot):
        self.bot = bot
        self.pattern = re.compile(
            r"\b(?:i['’]?m|i\s+am)\s+([^,.\n!?;]+)",
            re.IGNORECASE,
        )
        self.url = "https://official-joke-api.appspot.com/jokes/random"
        self._candidates: list[Callable[[], Awaitable[str | None]]] = [
            self.appspot,
            self.icanhazdadjoke,
            self.jokeapi,
        ]

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        match = self.pattern.search(message.content)
        if not match:
            return

        # Extract the captured text and limit length to prevent massive spam walls
        extracted = match.group(1).strip()
        if not extracted or len(extracted) > 50:
            return

        joke = f"Hello {extracted}, I am {self.bot.name}!"
        french = await self.bot.french(joke)
        await message.channel.send(french)

    @commands.command()
    async def dad(self, ctx: commands.Context):
        """Has two functionalities
        1. Fetches a random dad joke.
        2. Makes a dad joke whenever user write I'm or I am in their message."""

        while True:
            if len(self._candidates) == 0:
                return await ctx.send("All sources are down. Try again later!")
            random.shuffle(self._candidates)
            joke = await self._candidates[0]()
            if joke is None:
                self._candidates.pop(0)
            else:
                return await self.bot.send_french(ctx, joke)

    async def appspot(self) -> str | None:
        url = "https://official-joke-api.appspot.com/jokes/random"
        try:
            setup, punchline = await self.bot.fetch(url, ["setup", "punchline"])
            return setup + "\n" + punchline
        except Exception as err:  # noqa
            return None

    async def icanhazdadjoke(self) -> str | None:
        url = "https://icanhazdadjoke.com/"
        try:
            response = await self.bot.fetch(url, "joke", {"Accept": "application/json"})
            return response
        except Exception as err:  # noqa
            return None

    async def jokeapi(self) -> str | None:
        url = "https://v2.jokeapi.dev/joke/Any?safe-mode"
        try:
            response = await self.bot.fetch(url)
            type = response["type"]
            if type == "twopart":
                msg = response["setup"] + "\n" + response["delivery"]
            else:
                msg = response["joke"]
            return msg
        except Exception as err:  # noqa
            return None


async def setup(bot: ViBot) -> None:
    await bot.add_cog(Dad(bot))

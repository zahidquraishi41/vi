import os
from typing import Any

import aiohttp
import discord
from discord.ext import commands

from main import ViBot


class Search(commands.Cog):
    """Web search cog powered by the Tavily Search API."""

    def __init__(self, bot: ViBot):
        self.bot = bot
        self.api_url = "https://api.tavily.com/search"
        self.api_key = os.getenv("TAVILY_API_KEY", "").strip()
        self.session = aiohttp.ClientSession()
        self._cache: dict[str, dict[str, Any]] = {}

    async def cog_unload(self) -> None:
        await self.session.close()

    async def _tavily_search(self, query: str, max_results: int = 1) -> dict[str, Any]:
        cache_key = query.lower()
        if cache_key in self._cache:
            return self._cache[cache_key]

        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "include_answer": True,
            "max_results": max_results,
        }

        async with self.session.post(self.api_url, json=payload) as resp:
            resp.raise_for_status()
            data: dict[str, Any] = await resp.json()

        self._cache[cache_key] = data
        return data

    @commands.command(name="search", aliases=["find", "web"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def search(self, ctx: commands.Context, *, query: str | None = None) -> None:
        """Searches the web and returns an instant answer with top sources.

        Usage:
            vivy search how many stars are in the sky
        """
        if not self.api_key:
            await self.bot.send_french(
                ctx, "❌ `TAVILY_API_KEY` is missing from your environment."
            )
            return

        if not query or not query.strip():
            await self.bot.send_french(ctx, "Please provide something to search for!")
            return

        clean_query = query.strip()

        try:
            data = await self._tavily_search(clean_query, max_results=1)
        except Exception as err:  # noqa: BLE001
            err_msg = str(err) or f"Unexpected error ({type(err).__name__})"
            await self.bot.send_french(ctx, f"❌ Search failed: {err_msg}")
            return

        answer = str(data.get("answer") or "").strip()
        results: list[dict[str, Any]] = data.get("results") or []

        if not answer and not results:
            await self.bot.send_french(ctx, f"No results found for **{clean_query}**.")
            return

        embed = discord.Embed(
            title=f"🔎 {clean_query}",
            color=discord.Color.blurple(),
        )

        if answer:
            translated_answer = await self.bot.french(answer)
            if len(translated_answer) > 1000:
                translated_answer = f"{translated_answer[:997]}..."
            embed.description = translated_answer

        for item in results[:3]:
            raw_title = str(item.get("title") or "Source").strip()
            raw_content = str(item.get("content") or "").strip()
            url = str(item.get("url") or "").strip()

            title = await self.bot.french(raw_title)
            snippet = await self.bot.french(raw_content) if raw_content else ""
            if len(snippet) > 220:
                snippet = f"{snippet[:217]}..."

            value = f"{snippet}\n[Read more]({url})" if url else snippet
            embed.add_field(name=title[:256], value=value[:1024] or "—", inline=False)

        footer = await self.bot.french("Results via Tavily")
        embed.set_footer(text=footer)

        await ctx.send(embed=embed)


async def setup(bot: ViBot) -> None:
    await bot.add_cog(Search(bot))

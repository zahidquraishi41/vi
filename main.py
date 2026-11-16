import asyncio
import html
import logging
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

from help import DocstringHelpCommand

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
logger = logging.getLogger(__name__)


# TEST THE FRENCH IS WORKIN OR NO
class ViBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(
            command_prefix=commands.when_mentioned_or("vi ", "vava "),
            intents=intents,
            help_command=DocstringHelpCommand(),
        )
        self.session: aiohttp.ClientSession | None = None
        self.name = self.user.display_name if self.user else "bot"
        self.french_enabled: bool = True
        self._french_cache = {
            "I need at least two distinct options to decide!": "Il me faut au moins deux options distinctes pour prendre une décision !",
            "Invalid category!": "Catégorie invalide !",
            "All sources are down. Try again later!": "Toutes les sources sont indisponibles. Réessayez plus tard !",
            "A riddle is already active in this channel!": "Une énigme est déjà en cours sur ce canal !",
            "Could not load a riddle right now.": "Impossible de charger une énigme pour le moment.",
            "A trivia game is already active in this channel!": "Un jeu de questions-réponses est déjà en cours sur ce canal !",
            "Could not load trivia questions at this time.": "Impossible de charger les questions de quiz pour le moment.",
        }

    async def on_command(self, ctx: commands.Context) -> None:
        """Logs invoked commands in guilds only (DMs are already logged in on_message)."""
        if ctx.guild is not None:
            print(f"[IN  | #{ctx.channel}] {ctx.author}: {ctx.message.content}")

    async def on_message(self, message: discord.Message) -> None:
        """Logs all DM messages, all outgoing bot messages, and processes commands."""
        # 1. Log outgoing bot messages (both Guild and DM)
        if self.user is not None and message.author.id == self.user.id:
            location = f"#{message.channel}" if message.guild else "DM"

            if message.content:
                print(f"[OUT | {location}] {message.content}")

            for embed in message.embeds:
                summary = embed.title or embed.description or "(Embed)"
                print(f"[OUT | {location}] [Embed] {summary}")
            return

        # 2. Log every incoming message in DMs (commands and regular chat)
        if message.guild is None:
            content = message.content or "[Attachment/Embed]"
            print(f"[IN  | DM] {message.author}: {content}")

        await self.process_commands(message)

    def _chunk_text(self, text: str, max_chars: int = 450) -> list[str]:
        """Splits text into chunks under max_chars without cutting words in half."""
        words = text.split(" ")
        chunks: list[str] = []
        current_chunk: list[str] = []
        current_len = 0

        for word in words:
            word_len = len(word) + 1  # accounts for space
            if current_len + word_len > max_chars:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = [word]
                    current_len = len(word)
                else:
                    # Single word exceeds max_chars; hard-split it
                    chunks.append(word)
                    current_chunk = []
                    current_len = 0
            else:
                current_chunk.append(word)
                current_len += word_len

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    async def french(self, text: str) -> str:
        """Translates English text to French."""
        if not self.french_enabled or not text or not text.strip():
            return text

        if text in self._french_cache:
            return self._french_cache[text]

        chunks = self._chunk_text(text.strip())
        translated_chunks: list[str] = []

        for idx, chunk in enumerate(chunks):
            if idx > 0:
                await asyncio.sleep(0.4)

            encoded_text = quote(chunk)
            url = f"https://api.mymemory.translated.net/get?q={encoded_text}&langpair=en|fr"

            try:
                translated_part = await self.fetch(url, "responseData.translatedText")
                if isinstance(translated_part, str) and translated_part:
                    translated_chunks.append(html.unescape(translated_part))
                else:
                    translated_chunks.append(chunk)
            except Exception as err:  # noqa
                logger.debug(f"French translation failed: {err}")
                translated_chunks.append(chunk)

        return " ".join(translated_chunks)

    async def send_french(self, ctx: commands.Context, text: str) -> None:
        """Translates English text to French and send it"""
        french = await self.french(text)
        await ctx.send(french)

    async def fetch(
        self,
        url: str,
        keys: str | list[str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Asynchronously fetches JSON data and extracts values via dot-notation path keys.

        Args:
            url: The HTTP endpoint to query.
            target_keys: A single dot-notation key (e.g. "slip.advice") or a sequence of keys.
            custom_headers: Optional HTTP headers to include with the request.
            timeout_seconds: Total request timeout duration in seconds.

        Returns:
            Extracted value if target_keys is a string, a list of values if target_keys is a sequence,
            or the entire parsed JSON payload if target_keys is None.
        """
        if not self.session:
            raise RuntimeError("ClientSession is not initialized.")

        async with self.session.get(url, params=params) as response:
            response.raise_for_status()
            payload = await response.json(content_type=None)

        if keys is None:
            return payload

        is_single_key = isinstance(keys, str)
        key_queries: list[str] = [keys] if is_single_key else list(keys)

        extracted_results: list[Any] = []

        for key_path in key_queries:
            path_segments = key_path.split(".")
            current_node = payload

            for segment in path_segments:
                if isinstance(current_node, list) and segment.isdigit():
                    current_node = current_node[int(segment)]
                elif isinstance(current_node, dict):
                    current_node = current_node[segment]
                else:
                    raise TypeError(
                        f"Cannot navigate segment '{segment}' on non-container node "
                        f"of type '{type(current_node).__name__}'"
                    )

            extracted_results.append(current_node)

        return extracted_results[0] if is_single_key else extracted_results

    async def setup_hook(self):
        self.session = aiohttp.ClientSession()

        cogs_dir = Path("./cogs")
        if cogs_dir.exists() and cogs_dir.is_dir():
            for file_path in cogs_dir.glob("*.py"):
                if file_path.name.startswith("__"):
                    continue
                try:
                    await self.load_extension(f"{cogs_dir.name}.{file_path.stem}")
                    print(f"Loaded extension: {file_path.stem}")
                except Exception as err:  # noqa
                    print(f"Failed to load extension {file_path.stem}: {err}")

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
        await super().close()

    async def on_ready(self):
        print(f"Logged in as {self.user}")


async def main():
    if TOKEN is None:
        raise ValueError("Error: DISCORD_TOKEN is missing from your .env file.")
    async with ViBot() as bot:
        await bot.start(TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCancelled by user")

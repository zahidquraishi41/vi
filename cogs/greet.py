import csv
import random
from dataclasses import dataclass
from pathlib import Path

import discord
from discord.ext import commands

from main import ViBot

CSV_PATH = Path("data/greetings.csv")
MAX_HISTORY = 50


@dataclass(frozen=True, slots=True)
class Greeting:
    language: str
    hello: str
    speakers: str
    region: str
    hello_roman: str
    hello_pronunciation: str


class Greetings(commands.Cog):
    def __init__(self, bot: ViBot) -> None:
        self.bot = bot
        self.greetings: list[Greeting] = self._load_greetings(CSV_PATH)
        self._message_history: dict[int, Greeting] = {}
        self._channel_history: dict[int, Greeting] = {}

    @staticmethod
    def _load_greetings(path: Path) -> list[Greeting]:
        if not path.exists():
            raise FileNotFoundError(f"Greetings CSV not found at {path.resolve()}")

        entries: list[Greeting] = []
        with path.open(mode="r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                language = (row.get("language") or "").strip()
                hello = (row.get("hello") or "").strip()
                if not language or not hello:
                    continue

                entries.append(
                    Greeting(
                        language=language,
                        hello=hello,
                        speakers=(row.get("speakers") or "Unknown").strip(),
                        region=(row.get("region") or "Unknown").strip(),
                        hello_roman=(row.get("hello_roman") or "").strip(),
                        hello_pronunciation=(
                            row.get("hello_pronunciation") or ""
                        ).strip(),
                    )
                )
        return entries

    def _get_random_greeting(self) -> Greeting | None:
        return random.choice(self.greetings) if self.greetings else None

    def _record_greeting(self, message: discord.Message, entry: Greeting) -> None:
        # Store by sent message ID (capped at MAX_HISTORY) and update channel fallback
        if message.id in self._message_history:
            del self._message_history[message.id]
        elif len(self._message_history) >= MAX_HISTORY:
            oldest_id = next(iter(self._message_history))
            del self._message_history[oldest_id]

        self._message_history[message.id] = entry
        self._channel_history[message.channel.id] = entry

    @staticmethod
    def _format_short_greeting(
        entry: Greeting,
        target: discord.Member | discord.User | None = None,
    ) -> str:
        text = entry.hello
        if entry.hello_roman and entry.hello_roman.lower() != entry.hello.lower():
            text = f"{entry.hello} ({entry.hello_roman})"

        return f"{target.mention} **{text}**!" if target else f"**{text}**!"

    @staticmethod
    def _build_info_embed(entry: Greeting) -> discord.Embed:
        embed = discord.Embed(
            title=f"{entry.language} — {entry.hello}",
            color=discord.Color.blurple(),
        )

        if entry.hello_roman and entry.hello_roman.lower() != entry.hello.lower():
            embed.add_field(name="Romanized", value=entry.hello_roman, inline=True)

        if entry.hello_pronunciation:
            embed.add_field(
                name="Pronunciation",
                value=f"`{entry.hello_pronunciation}`",
                inline=True,
            )

        embed.add_field(name="Region", value=entry.region, inline=True)
        embed.add_field(name="Speakers", value=entry.speakers, inline=True)
        return embed

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or self.bot.user is None:
            return

        content = message.content.strip().lower()
        triggers = {
            "vi",
            "vava",
            f"<@{self.bot.user.id}>",
            f"<@!{self.bot.user.id}>",
        }
        if content not in triggers:
            return

        entry = self._get_random_greeting()
        if entry is None:
            return

        sent = await message.reply(
            self._format_short_greeting(entry),
            mention_author=False,
        )
        self._record_greeting(sent, entry)

    @commands.command(name="greetings")
    async def greetings_command(self, ctx: commands.Context[commands.Bot]) -> None:
        """Respond with a greeting in a random language."""
        entry = self._get_random_greeting()
        if entry is None:
            await ctx.send("No greetings are currently loaded.")
            return

        sent = await ctx.send(self._format_short_greeting(entry))
        self._record_greeting(sent, entry)

    @commands.command(name="greet")
    async def greet_user_command(
        self,
        ctx: commands.Context[ViBot],
        member: discord.Member,
    ) -> None:
        """Greet a user in a random language."""
        entry = self._get_random_greeting()
        if entry is None:
            await ctx.send("No greetings are currently loaded.")
            return

        sent = await ctx.send(
            content=self._format_short_greeting(entry, target=member),
            allowed_mentions=discord.AllowedMentions(users=[member]),
        )
        self._record_greeting(sent, entry)

    @commands.command(name="greetinfo", aliases=["info", "greetinginfo"])
    async def greet_info_command(self, ctx: commands.Context[ViBot]) -> None:
        """Show details for a replied greeting or the latest greeting in this channel."""
        entry: Greeting | None = None

        # 1. Check if the user replied directly to a tracked greeting message
        ref = ctx.message.reference
        if ref is not None and ref.message_id is not None:
            entry = self._message_history.get(ref.message_id)
            if entry is None:
                await ctx.send("I don't have details cached for that specific message.")
                return

        # 2. Fall back to the most recent greeting sent in the current channel
        if entry is None:
            entry = self._channel_history.get(ctx.channel.id)

        if entry is None:
            await ctx.send("No recent greeting found in this channel.")
            return

        await ctx.send(embed=self._build_info_embed(entry))

    @greet_user_command.error
    async def greet_user_error(
        self,
        ctx: commands.Context[ViBot],
        error: commands.CommandError,
    ) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Specify who to greet! Example: `vivy greet @user`")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("I couldn't find that user in this server.")
        else:
            raise error


async def setup(bot: ViBot) -> None:
    await bot.add_cog(Greetings(bot))

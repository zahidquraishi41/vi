import random
import re
from dataclasses import dataclass, field

import discord
from discord.ext import commands

from main import ViBot


@dataclass
class ActiveRiddle:
    question: str
    answer: str
    hint_level: int = 0
    revealed_indices: set[int] = field(default_factory=set)

    def next_hint(self) -> str:
        """Generates the next progressive hint mask for the answer."""
        self.hint_level += 1
        chars = list(self.answer)
        letter_indices = [i for i, ch in enumerate(chars) if ch.isalnum()]

        # Level 1: Reveal nothing yet, just show word/letter structure
        if self.hint_level == 1:
            pass

        # Level 2: Reveal the first character of every word
        elif self.hint_level == 2:
            for idx, ch in enumerate(chars):
                if ch.isalnum() and (idx == 0 or not chars[idx - 1].isalnum()):
                    self.revealed_indices.add(idx)

        # Level 3+: Reveal ~40% of remaining unrevealed letters each click
        else:
            unrevealed = [i for i in letter_indices if i not in self.revealed_indices]
            if unrevealed:
                step = max(1, len(letter_indices) // 3)
                self.revealed_indices.update(
                    random.sample(unrevealed, min(step, len(unrevealed)))
                )

        masked = []
        for idx, ch in enumerate(chars):
            if not ch.isalnum():
                masked.append("  " if ch == " " else ch)
            elif idx in self.revealed_indices:
                masked.append(ch)
            else:
                masked.append("_")

        words = [w for w in re.split(r"\s+", self.answer.strip()) if w]
        mask_str = " ".join(masked)
        return f"`{mask_str}` ({len(words)} word{'s' if len(words) != 1 else ''}, {len(letter_indices)} letters)"


class RiddleView(discord.ui.View):
    """Interactive buttons for requesting hints or revealing the answer."""

    def __init__(self, bot: ViBot, cog: "Riddle", channel_id: int, timeout: float = 60.0):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.cog = cog
        self.channel_id = channel_id
        self.message: discord.Message | None = None

    def _disable_all(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

    @discord.ui.button(label="💡 Hint", style=discord.ButtonStyle.primary)
    async def hint_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        game = self.cog.active_riddles.get(self.channel_id)
        if game is None:
            msg = await self.bot.french("This riddle has already ended.")
            await interaction.response.send_message(msg, ephemeral=True)
            return

        hint_text = game.next_hint()
        hint_label = await self.bot.french("Hint")

        # Cap at 3 hints so users still have to guess the final letters
        if game.hint_level >= 3:
            button.disabled = True

        if interaction.message and interaction.message.embeds:
            embed = interaction.message.embeds[0]
            # Update existing Hint field or add a new one
            if embed.fields:
                embed.set_field_at(
                    0,
                    name=f"💡 {hint_label} ({game.hint_level}/3)",
                    value=hint_text,
                    inline=False,
                )
            else:
                embed.add_field(
                    name=f"💡 {hint_label} ({game.hint_level}/3)",
                    value=hint_text,
                    inline=False,
                )
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message(f"💡 {hint_text}")

    @discord.ui.button(label="🏳️ Give Up", style=discord.ButtonStyle.secondary)
    async def give_up_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        game = self.cog.active_riddles.pop(self.channel_id, None)
        if game is None:
            return

        self._disable_all()
        self.stop()

        if interaction.message and interaction.message.embeds:
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.orange()
            reveal_text = await self.bot.french("The answer was:")
            embed.add_field(
                name="🏳️ Revealed",
                value=f"{reveal_text} **{game.answer}**",
                inline=False,
            )
            await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self) -> None:
        game = self.cog.active_riddles.pop(self.channel_id, None)
        if game is None or self.message is None or not self.message.embeds:
            return

        self._disable_all()
        embed = self.message.embeds[0]
        embed.color = discord.Color.dark_grey()
        timeout_text = await self.bot.french("Time's up! The answer was:")
        embed.add_field(
            name="⏰ Expired",
            value=f"{timeout_text} **{game.answer}**",
            inline=False,
        )
        try:
            await self.message.edit(embed=embed, view=self)
        except discord.HTTPException:
            pass


class Riddle(commands.Cog):
    """Asks random riddles with progressive hints."""

    def __init__(self, bot: ViBot):
        self.bot = bot
        self.url = "https://riddles-api.vercel.app/random"
        self.active_riddles: dict[int, ActiveRiddle] = {}

    @staticmethod
    def _normalize(text: str) -> str:
        """Strips punctuation, articles, and casing for forgiving answer checks."""
        cleaned = re.sub(r"[^\w\s]", "", text.lower()).strip()
        cleaned = re.sub(r"^(a|an|the|un|une|le|la|les)\s+", "", cleaned)
        return cleaned

    @commands.command(name="riddle")
    async def riddle(self, ctx: commands.Context) -> None:
        """Starts a riddle in the current channel with interactive hints."""
        if ctx.channel.id in self.active_riddles:
            await self.bot.send_french(
                ctx, "A riddle is already active in this channel!"
            )
            return

        try:
            data = await self.bot.fetch(self.url)
        except Exception as err:  # noqa: BLE001
            err_msg = str(err) or f"Unexpected error ({type(err).__name__})"
            await self.bot.send_french(ctx, f"Failed to fetch riddle: {err_msg}")
            return

        if not isinstance(data, dict) or "riddle" not in data or "answer" not in data:
            await self.bot.send_french(ctx, "Could not load a riddle right now.")
            return

        question = await self.bot.french(str(data["riddle"]).strip())
        # Keep answer aligned with active language mode so hints match user guesses
        answer = await self.bot.french(str(data["answer"]).strip())

        game = ActiveRiddle(question=question, answer=answer)
        self.active_riddles[ctx.channel.id] = game

        title = await self.bot.french("🧩 Riddle Time!")
        footer = await self.bot.french("Type your guess in chat or click Hint!")

        embed = discord.Embed(
            title=title,
            description=f"**{question}**",
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=footer)

        view = RiddleView(bot=self.bot, cog=self, channel_id=ctx.channel.id)
        message = await ctx.send(embed=embed, view=view)
        view.message = message

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        game = self.active_riddles.get(message.channel.id)
        if game is None:
            return

        if self._normalize(message.content) == self._normalize(game.answer):
            self.active_riddles.pop(message.channel.id, None)
            win_msg = await self.bot.french("got it right! The answer was:")
            await message.reply(
                f"🎉 {message.author.mention} {win_msg} **{game.answer}**"
            )


async def setup(bot: ViBot) -> None:
    await bot.add_cog(Riddle(bot))

import html
import random
from collections.abc import Sequence

import discord
from discord.ext import commands

from main import ViBot


class FastestFingerTriviaView(discord.ui.View):
    """View where the first user to click locks in their answer immediately."""

    def __init__(
        self,
        bot: ViBot,
        correct_answer: str,
        options: Sequence[str],
        is_boolean: bool,
        timeout: float = 30.0,
    ):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.correct_answer = correct_answer
        self.options = options
        self.answered: bool = False
        self.message: discord.Message | None = None

        labels = ["True", "False"] if is_boolean else ["A", "B", "C", "D"]

        for idx, label in enumerate(labels):
            button = discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.secondary,
                custom_id=f"trivia_{idx}",
            )
            button.callback = self._create_callback(button, self.options[idx])
            self.add_item(button)

    def _create_callback(self, button: discord.ui.Button, choice_text: str):
        async def callback(interaction: discord.Interaction):
            if self.answered:
                warning = await self.bot.french("⚠️ Someone already answered!")
                await interaction.response.send_message(warning, ephemeral=True)
                return

            message = interaction.message
            if message is None or not message.embeds:
                return

            self.answered = True
            self.stop()

            user = interaction.user
            is_correct = choice_text == self.correct_answer

            # Disable all buttons and highlight selections
            for idx, item in enumerate(self.children):
                if isinstance(item, discord.ui.Button):
                    item.disabled = True
                    if self.options[idx] == self.correct_answer:
                        item.style = discord.ButtonStyle.success
                    elif item == button and not is_correct:
                        item.style = discord.ButtonStyle.danger

            embed = message.embeds[0]
            curr_desc = embed.description or ""

            if is_correct:
                embed.color = discord.Color.green()
                title_suffix = await self.bot.french("got it right!")
                answer_label = await self.bot.french("Answer:")
                buzz_text = await self.bot.french(
                    "buzzed in first and answered correctly!"
                )
                embed.title = f"🎉 {user.display_name} {title_suffix}"
                embed.description = (
                    f"{curr_desc}\n\n"
                    f"**{answer_label}** **{self.correct_answer}**\n"
                    f"⚡ {user.mention} {buzz_text}"
                )
            else:
                embed.color = discord.Color.red()
                title_suffix = await self.bot.french("got it wrong!")
                answer_label = await self.bot.french("Correct Answer:")
                buzz_text = await self.bot.french("buzzed in first with")
                embed.title = f"❌ {user.display_name} {title_suffix}"
                embed.description = (
                    f"{curr_desc}\n\n"
                    f"**{answer_label}** **{self.correct_answer}**\n"
                    f"⚡ {user.mention} {buzz_text} **{choice_text}**."
                )

            await interaction.response.edit_message(embed=embed, view=self)

        return callback

    async def on_timeout(self) -> None:
        """Handles expiration if nobody buzzes in within 30 seconds."""
        if self.answered:
            return

        message = self.message
        if message is None or not message.embeds:
            return

        for idx, item in enumerate(self.children):
            if isinstance(item, discord.ui.Button):
                item.disabled = True
                if self.options[idx] == self.correct_answer:
                    item.style = discord.ButtonStyle.success

        embed = message.embeds[0]
        curr_desc = embed.description or ""

        embed.color = discord.Color.dark_grey()
        embed.title = await self.bot.french("⏰ Time's Up!")
        timeout_msg = await self.bot.french(
            "Nobody buzzed in! The correct answer was"
        )
        embed.description = (
            f"{curr_desc}\n\n"
            f"{timeout_msg} **{self.correct_answer}**."
        )

        try:
            await message.edit(embed=embed, view=self)
        except discord.HTTPException:
            pass


class Trivia(commands.Cog):
    """Cog for running fast-paced trivia games with sticky difficulty."""

    def __init__(self, bot: ViBot):
        self.bot = bot
        self.default_difficulty: str = "easy"
        self.queues: dict[str, list[dict]] = {
            "easy": [],
            "medium": [],
            "hard": [],
        }
        self.active_channels: set[int] = set()

    async def _fetch_next_question(self, difficulty: str) -> dict | None:
        """Pulls from the corresponding difficulty queue; refills on exhaustion."""
        queue = self.queues.get(difficulty)
        if queue is None:
            return None

        if not queue:
            url = f"https://opentdb.com/api.php?amount=10&difficulty={difficulty}"
            data = await self.bot.fetch(url)
            if not isinstance(data, dict) or data.get("response_code") != 0:
                return None
            self.queues[difficulty] = data.get("results", [])
            queue = self.queues[difficulty]

        return queue.pop(0) if queue else None

    @commands.command(name="trivia")
    async def trivia(
        self,
        ctx: commands.Context,
        difficulty: str | None = None,
    ):
        """Play fastest-finger trivia. Passing a difficulty sets it as the new default.

        Usage:
            vivy trivia
            vivy trivia easy
            vivy trivia medium
            vivy trivia hard
        """
        if difficulty is not None:
            diff_key = difficulty.lower().strip()
            if diff_key not in self.queues:
                await self.bot.send_french(
                    ctx,
                    "❌ Invalid difficulty! Please choose `easy`, `medium`, or `hard`.",
                )
                return
            self.default_difficulty = diff_key

        active_diff = self.default_difficulty

        if ctx.channel.id in self.active_channels:
            await self.bot.send_french(
                ctx, "A trivia game is already active in this channel!"
            )
            return

        try:
            question_data = await self._fetch_next_question(active_diff)
        except Exception as err:  # noqa: BLE001
            err_msg = str(err) or f"Unexpected error ({type(err).__name__})"
            await self.bot.send_french(
                ctx, f"❌ Failed to reach trivia service: {err_msg}"
            )
            return

        if not question_data:
            await self.bot.send_french(
                ctx, "Could not load trivia questions at this time."
            )
            return

        self.active_channels.add(ctx.channel.id)

        try:
            raw_category = html.unescape(question_data.get("category", "General"))
            q_type = question_data.get("type", "multiple")
            raw_question = html.unescape(question_data.get("question", ""))
            raw_correct = html.unescape(question_data.get("correct_answer", ""))
            raw_incorrect = [
                html.unescape(ans) for ans in question_data.get("incorrect_answers", [])
            ]

            category = await self.bot.french(raw_category)
            question_text = await self.bot.french(raw_question)
            title_text = await self.bot.french("⚡ Fastest Finger Trivia!")
            footer_text = await self.bot.french(
                f"Category: {category} • Difficulty: {active_diff.capitalize()} • First to click wins!"
            )

            embed = discord.Embed(
                title=title_text,
                color=discord.Color.blurple(),
            )
            embed.set_footer(text=footer_text)

            if q_type == "boolean":
                is_true = raw_correct.lower() == "true"
                options = [
                    await self.bot.french("True"),
                    await self.bot.french("False"),
                ]
                correct_answer = options[0] if is_true else options[1]
                prompt = await self.bot.french("First to click True or False wins:")

                embed.description = f"**{question_text}**\n\n*{prompt}*"
                view = FastestFingerTriviaView(
                    bot=self.bot,
                    correct_answer=correct_answer,
                    options=options,
                    is_boolean=True,
                )
            else:
                correct_answer = await self.bot.french(raw_correct)
                incorrect_answers = [
                    await self.bot.french(ans) for ans in raw_incorrect
                ]
                options = incorrect_answers + [correct_answer]
                random.shuffle(options)

                letters = ["A", "B", "C", "D"]
                formatted_choices = "\n".join(
                    f"**{letters[i]}:** {options[i]}" for i in range(len(options))
                )
                prompt = await self.bot.french("First to buzz in wins:")

                embed.description = (
                    f"**{question_text}**\n\n{formatted_choices}\n\n*{prompt}*"
                )
                view = FastestFingerTriviaView(
                    bot=self.bot,
                    correct_answer=correct_answer,
                    options=options,
                    is_boolean=False,
                )

            message = await ctx.send(embed=embed, view=view)
            view.message = message

            await view.wait()

        finally:
            self.active_channels.discard(ctx.channel.id)


async def setup(bot: ViBot) -> None:
    await bot.add_cog(Trivia(bot))

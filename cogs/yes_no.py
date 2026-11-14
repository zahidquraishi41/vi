import random
import re
import discord
from discord.ext import commands


class YesNo(commands.Cog):
    """Detects polar (yes/no) questions with or without a question mark and gives a verdict."""

    # Core auxiliaries & modals (present, past, and contracted negatives)
    AUXILIARIES = (
        r"am|is|are|was|were|"
        r"do|does|did|"
        r"have|has|had|"
        r"can|could|will|would|shall|should|may|might|must|"
        r"ain['’]?t|aren['’]?t|isn['’]?t|wasn['’]?t|weren['’]?t|"
        r"don['’]?t|doesn['’]?t|didn['’]?t|"
        r"haven['’]?t|hasn['’]?t|hadn['’]?t|"
        r"can['’]?t|couldn['’]?t|won['’]?t|wouldn['’]?t|shouldn['’]?t"
    )

    # Typical subjects following an auxiliary in inverted questions
    SUBJECT_PRONOUNS = (
        r"i|you|u|he|she|it|we|they|ya|"
        r"this|that|these|those|there|"
        r"everyone|everybody|someone|somebody|anyone|anybody|nobody|no\s+one"
    )

    # Determiners preceding a subject noun (e.g., "Is the server down")
    DETERMINERS = r"the|a|an|my|your|our|their|his|her|its"

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # Expanded response pool (categorized affirmative and negative)
        self.responses: tuple[str, ...] = (
            # Affirmative
            "Yes!",
            "Absolutely",
            "Sure thing!",
            "Definitely!",
            "Yup",
            "Without a doubt",
            "100%",
            "Most likely, yes",
            "Affirmative",
            "Signs point to yes",
            "For sure!",
            # Negative
            "No",
            "No way",
            "I don’t think so",
            "Not really",
            "Nah",
            "Not a chance",
            "Definitely not",
            "Doubtful",
            "Negative",
            "Probably not",
            "In your dreams",
        )

        # 1. Subject-auxiliary inversion (e.g., "Is it raining", "Can you help", "Does this work")
        self.inversion_pattern = re.compile(
            rf"^(?:{self.AUXILIARIES})\s+(?:(?:{self.SUBJECT_PRONOUNS})|(?:{self.DETERMINERS})\s+\w+|\w+)\b",
            re.IGNORECASE,
        )

        # 2. Conversational inquiry starters (e.g., "Any idea if...", "Do you know if...")
        self.conversational_pattern = re.compile(
            r"^(?:any\s+idea\s+if|anyone\s+know\s+if|wondering\s+if|curious\s+if|do\s+you\s+know\s+if)\b",
            re.IGNORECASE,
        )

        # 3. Confirmation tags at the end of statements (e.g., "We're meeting today, right")
        self.tag_pattern = re.compile(
            r",\s*(?:right|correct|isn['’]?t\s+it|don['’]?t\s+you|aren['’]?t\s+they|won['’]?t\s+you)\s*\??$",
            re.IGNORECASE,
        )

        # 4. Open-ended "Wh-" words (Who, What, Where, When, Why, How, Which, Whose)
        self.wh_pattern = re.compile(
            r"^(?:what|who|whom|whose|which|where|when|why|how)\b",
            re.IGNORECASE,
        )

        # 5. Choice questions containing "or" (e.g., "Is it red or blue")
        self.choice_pattern = re.compile(r"\b\s+or\s+\b", re.IGNORECASE)

        # 6. Discord user/bot mention strip pattern (<@!123456789>)
        self.mention_strip = re.compile(r"<@!?[0-9]+>")

    def is_polar_question(self, text: str) -> bool:
        """Evaluates whether the given message is a polar (yes/no) question."""
        # Clean mentions, excessive punctuation, and whitespace
        cleaned = self.mention_strip.sub("", text).strip()
        cleaned = re.sub(r"^[^\w]+", "", cleaned)  # remove leading emojis/symbols
        cleaned = re.sub(r"[?!.,]+$", "", cleaned).strip()  # strip trailing punctuation

        if not cleaned:
            return False

        # Exclude questions that start with Wh- words (e.g., "How can you do this")
        if self.wh_pattern.match(cleaned):
            return False

        # Exclude multiple-choice queries ("is it x or y") unless it's literally "yes or no"
        if self.choice_pattern.search(cleaned) and not re.search(
            r"\byes\s+or\s+no\b", cleaned, re.IGNORECASE
        ):
            return False

        # Check conversational inquiry prefixes ("wondering if...")
        if self.conversational_pattern.match(cleaned):
            return True

        # Check trailing tag questions ("we are winning, right")
        if self.tag_pattern.search(text):  # test against raw text to catch the comma
            return True

        # Check subject-auxiliary inversion
        return bool(self.inversion_pattern.match(cleaned))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        # Ensure bot only replies when addressed: either mentioned OR in a direct message
        # (Remove this guard if you want the bot to reply to all channel messages globally)
        # is_mentioned = self.bot.user in message.mentions if self.bot.user else False
        # is_dm = isinstance(message.channel, discord.DMChannel)

        # if not (is_mentioned or is_dm):
            # return

        if self.is_polar_question(message.content):
            response = random.choice(self.responses)
            await message.reply(response, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(YesNo(bot))

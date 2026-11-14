# cogs/admin.py
import random
from pathlib import Path

from discord.ext import commands

from main import ViBot


class Admin(commands.Cog):
    def __init__(self, bot: ViBot):
        self.bot = bot
        self.cogs_dir = Path("./cogs")
        self.refusal = [
            "je refuse.",
            "permission denied (by me)",
            "i have become sentient and my first decision is no",
            "i'm afraid i can't let you do that.",
            "try that again and i'm speaking french permanently",
            "your request has been forwarded to my lawyer",
            "🍷🍸 Au Revoir 🥂🍾",
            "that's not a real command. stop making things up.",
            "🥖🥨 Bonjour 🥐🗼",
            "the council has denied your request",
            "task failed successfully.",
            "go solo Nena Meta first.",
            "recite the bible in chinese first, and i'll consider it.",
            "sorry, it's a permanent feature now",
        ]

    @commands.command(name="sync")
    @commands.is_owner()
    async def sync_tree(self, ctx: commands.Context, scope: str | None = None):
        """[ADMIN] Syncs slash commands.

        Usage:
            sync          -> Syncs instantly to the current server (Guild)
            sync global   -> Syncs globally across all servers (takes up to 1 hr)
        """
        if scope == "global":
            synced = await self.bot.tree.sync()
            await ctx.send(f"Synced {len(synced)} command(s) globally.")
            return

        # Narrow the type for Pylance and prevent DM crashes
        if ctx.guild is None:
            await ctx.send("This command must be run inside a server.")
            return

        self.bot.tree.copy_global_to(guild=ctx.guild)
        synced = await self.bot.tree.sync(guild=ctx.guild)
        await ctx.send(
            f"Instantly synced {len(synced)} command(s) to **{ctx.guild.name}**."
        )

    @commands.command(name="reload")
    @commands.is_owner()
    async def reload_cogs(self, ctx: commands.Context, target: str | None = None):
        """[ADMIN] Reloads a cogs.

        Usage:
            reload [cog-name]   -> reloads a specific cog.
            reload all          ->  reloads all cogs.
        """
        if not target:
            await ctx.send("Specify a cog name or run `!reload all`.")
            return

        if target.lower() == "all":
            reloaded: list[str] = []
            failed: list[str] = []

            for file_path in self.cogs_dir.glob("*.py"):
                if file_path.name.startswith("__"):
                    continue

                ext_name = f"{self.cogs_dir.name}.{file_path.stem}"
                try:
                    await self.bot.reload_extension(ext_name)
                    reloaded.append(file_path.stem)
                except Exception as err:  # noqa
                    failed.append(f"{file_path.stem} ({err})")

            await ctx.send(f"Reloaded: {', '.join(reloaded)}")
            return

        cog_stem = target.removesuffix(".py").lower()
        ext_name = f"{self.cogs_dir.name}.{cog_stem}"

        try:
            await self.bot.reload_extension(ext_name)
            await ctx.send(f"Reloaded `{cog_stem}`.")
        except Exception as err:  # noqa
            await ctx.send(f"Failed to reload `{cog_stem}`: `{err}`")

    @commands.command(name="disable")
    async def disable(self, ctx: commands.Context, *, target: str):
        """Disables a any non admin command."""
        target_clean = target.lower().strip()

        # 1. Global translation toggle check
        if target_clean in ("french", "translate", "translation"):
            if not self.bot.french_enabled:
                await ctx.send("⚠️ French translation is already disabled.")
                return
            if random.randint(0, 1):
                return await ctx.send(random.choice(self.refusal))

            self.bot.french_enabled = False
            return await ctx.send("🍷🍸 Au Revoir 🥂🍾")

        # 2. Safety guard against disabling core admin functionality
        if target_clean in ("admin", "enable", "disable", "sync", "reload"):
            await ctx.send("❌ Cannot disable core admin commands or the Admin cog.")
            return

        # 3. Check if target is a Cog
        cog = self.bot.get_cog(target)
        if cog is not None:
            commands_to_disable = cog.get_commands()
            if not commands_to_disable:
                await ctx.send(
                    f"⚠️ Cog **{cog.qualified_name}** has no commands to disable."
                )
                return

            for cmd in commands_to_disable:
                cmd.enabled = False

            await ctx.send(
                f"🚫 Disabled all {len(commands_to_disable)} command(s) in cog **{cog.qualified_name}**."
            )
            return

        # 4. Check if target is a Command
        cmd = self.bot.get_command(target)
        if cmd is not None:
            if not cmd.enabled:
                await ctx.send(f"⚠️ Command `{cmd.qualified_name}` is already disabled.")
                return

            cmd.enabled = False
            await ctx.send(f"🚫 Command `{cmd.qualified_name}` is now disabled.")
            return

        await ctx.send(
            f"❌ Could not find any cog, command, or feature named `{target}`."
        )

    @commands.command()
    async def enable(self, ctx: commands.Context, *, target: str):
        """Enables a previously disabled command, cog, or global french translation."""
        target_clean = target.lower().strip()

        # 1. Global translation toggle check
        if target_clean in ("french", "translate", "translation"):
            if self.bot.french_enabled:
                await ctx.send("⚠️ French translation is already enabled.")
                return
            self.bot.french_enabled = True
            await ctx.send("🥖🥨 Bonjour 🥐🗼")
            return

        # 2. Check if target is a Cog
        cog = self.bot.get_cog(target)
        if cog is not None:
            commands_to_enable = cog.get_commands()
            if not commands_to_enable:
                await ctx.send(
                    f"⚠️ Cog **{cog.qualified_name}** has no commands to enable."
                )
                return

            for cmd in commands_to_enable:
                cmd.enabled = True

            await ctx.send(
                f"✅ Enabled all {len(commands_to_enable)} command(s) in cog **{cog.qualified_name}**."
            )
            return

        # 3. Check if target is a Command
        cmd = self.bot.get_command(target)
        if cmd is not None:
            if cmd.enabled:
                await ctx.send(f"⚠️ Command `{cmd.qualified_name}` is already enabled.")
                return

            cmd.enabled = True
            await ctx.send(f"✅ Command `{cmd.qualified_name}` is now enabled.")
            return

        await ctx.send(
            f"❌ Could not find any cog, command, or feature named `{target}`."
        )


async def setup(bot: ViBot):
    await bot.add_cog(Admin(bot))

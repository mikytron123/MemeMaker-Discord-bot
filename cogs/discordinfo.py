from discord.ext import commands
import discord
from discord import app_commands
from decorators import timer_function, log_arguments


class DiscordInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="info", description="Extra info about the bot")
    @log_arguments
    @timer_function
    async def info(self, ctx: discord.Interaction):
        view = discord.ui.LayoutView()
        container = discord.ui.Container(
            discord.ui.TextDisplay("### Memebot Info"),
            discord.ui.TextDisplay("This bot is managed by visssion"),
            discord.ui.TextDisplay(
                "💻 Source Code:\n[Click Here](https://github.com/mikytron123/MemeMaker-Discord-bot)"
            ),
        )
        view = view.add_item(container)
        await ctx.response.send_message(view=view)


async def setup(bot):
    await bot.add_cog(DiscordInfo(bot))

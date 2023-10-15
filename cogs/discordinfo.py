from discord.ext import commands
import discord
from discord import app_commands
from decorators import timer_function, log_arguments


class DiscordInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="banner", description="Get user banner")
    @app_commands.describe(user="server member")
    @log_arguments
    @timer_function
    async def banner(self, ctx: discord.Interaction, user: discord.Member):
        banner = (await ctx.client.fetch_user(user.id)).banner
        if banner is None:
            await ctx.response.send_message(
                f"User {str(user)} does not have a banner", ephemeral=True
            )
        else:
            embed = discord.Embed(description="User Banner")
            embed.set_image(url=banner.url)
            embed.set_author(name=user.name, icon_url=user.default_avatar.url)
            await ctx.response.send_message(embed=embed)

    @app_commands.command(name="info", description="Extra info about the bot")
    @log_arguments
    @timer_function
    async def info(self, ctx: discord.Interaction):
        embed = discord.Embed(
            title="MemeBot Info", description="This bot is managed by visssion"
        )
        embed.add_field(
            name="💻 Source Code:",
            value="[Click Here](https://github.com/mikytron123/MemeMaker-Discord-bot)",
            inline=False,
        )
        await ctx.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(DiscordInfo(bot))

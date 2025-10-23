from io import BytesIO
from pathlib import Path
from typing import Optional
from discord.ext import commands
import discord
from discord import app_commands
import traceback
import tempfile
from apnggif import apnggif
from PIL import Image, ImageSequence

from decorators import timer_function, log_arguments

from image_handler import create_image_class
from layoutviews import RerollView
from utils import seekrandomframe


class GifCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="apng2gif", description="Convert apng file to gif")
    @app_commands.describe(file="apng file", link="direct url to apng file")
    @log_arguments
    @timer_function
    async def apng2gif(
        self,
        ctx: discord.Interaction,
        file: Optional[discord.Attachment] = None,
        link: str = "",
    ):
        await ctx.response.defer()
        try:
            img = await create_image_class(file, link, "png")
            filename = str(Path(img.get_filename()).with_suffix(".gif"))
            imagebytes = await img.get_image_bytes()

            with tempfile.NamedTemporaryFile(
                suffix=".png", delete_on_close=False
            ) as fp:
                with tempfile.NamedTemporaryFile(suffix=".gif") as fp2:
                    fp.write(imagebytes)
                    fp.close()
                    # convert to gif
                    apnggif(png=fp.name, gif=fp2.name)
                    filepath = str(Path(fp2.name).with_suffix(".gif"))
                    await ctx.followup.send(
                        file=discord.File(fp=filepath, filename=filename)
                    )

        except ValueError as v:
            print(v)
            await ctx.followup.send(str(v), ephemeral=True)
            return
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            await ctx.followup.send("Error converting to gif", ephemeral=True)

    @app_commands.command(name="giframe", description="Returns random frame from gif")
    @app_commands.describe(file="gif file", link="direct url link to gif")
    @log_arguments
    @timer_function
    async def giframe(
        self,
        ctx: discord.Interaction,
        file: Optional[discord.Attachment] = None,
        link: str = "",
    ):
        await ctx.response.defer()
        try:
            img = await create_image_class(file, link, "gif")
            imgbytes = await img.get_image_bytes()
            filename = str(Path(img.get_filename()).with_suffix(".png"))

            image_binary = seekrandomframe(imgbytes)
            # send final image
            view = RerollView(imgbytes, filename, image_binary)

            msg = await ctx.followup.send(
                file=discord.File(fp=image_binary, filename=filename), view=view
            )
            view.message = msg

        except ValueError as v:
            print(v)
            await ctx.followup.send(str(v), ephemeral=True)
            return

        except Exception as e:
            print(e)
            print(traceback.format_exc())
            await ctx.followup.send("Error generating random frame", ephemeral=True)

    @app_commands.command(name="reversegif", description="Reverses a gif")
    @app_commands.describe(file="gif file", link="direct url link to gif")
    @log_arguments
    @timer_function
    async def reversegif(
        self,
        ctx: discord.Interaction,
        file: Optional[discord.Attachment] = None,
        link: str = "",
    ):
        await ctx.response.defer()
        try:
            img = await create_image_class(file, link, "gif")
            imgbytes = await img.get_image_bytes()
            filename = img.get_filename()

            # read image from url
            gif = Image.open(BytesIO(imgbytes))
            frames: list = []

            for frame in ImageSequence.Iterator(gif):
                frames.append(frame.copy())

            # Reverse the frames
            frames.reverse()
            frame_one = frames[0]

            with BytesIO() as gif_binary:
                frame_one.save(
                    gif_binary,
                    format="GIF",
                    append_images=frames,
                    save_all=True,
                    loop=0,
                    disposal=2,
                )
                gif_binary.seek(0)
                await ctx.followup.send(
                    file=discord.File(
                        fp=gif_binary, filename=str(Path(filename).with_suffix(".gif"))
                    )
                )
        except ValueError as v:
            print(v)
            await ctx.followup.send(str(v), ephemeral=True)
            return

        except Exception as e:
            print(e)
            print(traceback.format_exc())
            await ctx.followup.send("Error reversing gif", ephemeral=True)


async def setup(bot):
    await bot.add_cog(GifCommands(bot))

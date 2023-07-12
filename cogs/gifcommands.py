from io import BytesIO
from pathlib import Path
from typing import Optional
from discord.ext import commands
import discord
from discord import app_commands
import traceback
from apnggif import apnggif
from PIL import Image, ImageDraw, ImageFont, ImageSequence

from utils import getimagedata, seekrandomframe
from views import RerollView

class GifCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="apng2gif", description="Convert apng file to gif")
    @app_commands.describe(file="apng file", link="direct url to apng file")
    async def apng2gif(
        self,
        ctx: discord.Interaction,
        file: Optional[discord.Attachment] = None,
        link: str = ""
    ):
        await ctx.response.defer()
        try:
            imagedata = await getimagedata(file, link, "png", ".png")
            error = imagedata.error

            if error != "":
                await ctx.followup.send(error, ephemeral=True)
                return

            imagebytes = imagedata.imagebytes
            filename = imagedata.filename

            with open(filename, "wb") as f:
                f.write(imagebytes)
            # convert to gif
            apnggif(filename)

            await ctx.followup.send(
                file=discord.File(str(Path(filename).with_suffix(".gif")))
            )
            # remove temporary file
            filepath = Path(filename)
            filepath.unlink()
            filepath = Path(filename).with_suffix(".gif")
            filepath.unlink()

        except Exception as e:
            print(e)
            print(traceback.format_exc())
            await ctx.followup.send("Error converting to gif", ephemeral=True)

    @app_commands.command(name="giframe", description="Returns random frame from gif")
    @app_commands.describe(file="gif file", link="direct url link to gif")
    async def giframe(self,
        ctx: discord.Interaction, file: Optional[discord.Attachment] = None, link: str = ""
    ):
        await ctx.response.defer()
        try:
            imagedata = await getimagedata(file, link, "gif", ".png")
            error = imagedata.error

            if error != "":
                await ctx.followup.send(error, ephemeral=True)
                return

            imgbytes = imagedata.imagebytes
            filename = imagedata.filename

            image_binary = await seekrandomframe(imgbytes)
            # send final image
            view = RerollView(imgbytes,filename)


            msg = await ctx.followup.send(
                    file=discord.File(fp=image_binary, filename=filename),
                    view=view
            )
            
            timeout = await view.wait()
            if timeout:
                if isinstance(msg, discord.WebhookMessage):
                    await msg.edit(view=None)  # type: ignore
                elif isinstance(msg, discord.Interaction):
                    await msg.edit_original_response(view=None)  # type: ignore

        except Exception as e:
            print(e)
            print(traceback.format_exc())
            await ctx.followup.send("Error generating random frame", ephemeral=True)

    @app_commands.command(name="reversegif", description="Reverses a gif")
    @app_commands.describe(file="gif file", link="direct url link to gif")
    async def reversegif(self,
        ctx: discord.Interaction, file: Optional[discord.Attachment] = None, link: str = ""
    ):
        await ctx.response.defer()
        try:
            imagedata = await getimagedata(file, link, "gif", ".gif")
            error = imagedata.error

            if error != "":
                await ctx.followup.send(error, ephemeral=True)
                return

            imgbytes = imagedata.imagebytes
            filename = imagedata.filename

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

        except Exception as e:
            print(e)
            print(traceback.format_exc())
            await ctx.followup.send("Error reversing gif", ephemeral=True)

async def setup(bot):
    await bot.add_cog(GifCommands(bot))

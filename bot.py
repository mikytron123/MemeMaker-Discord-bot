# bot.py
import aiohttp
from pyrlottie import run, convSingleLottie, LottieFile
import discord
import random
import uuid
import requests
import traceback
from PIL import Image, ImageDraw, ImageFont, ImageSequence
from apnggif import apnggif
from bs4 import BeautifulSoup
from discord import app_commands
from fontTools.ttLib import TTFont
from io import BytesIO
from pathlib import Path
import plotly.graph_objects as go
from typing import List, Dict, Callable, Optional, Any
from urllib.parse import urlparse

from config import read_configs
from dumpy import dumpy
from utils import getimagedata

import nest_asyncio

nest_asyncio.apply()

configs = read_configs(dev=False)
TOKEN: str = configs.token
MY_GUILDS: List[discord.Object] = configs.guilds


def has_glyph(font, glyph):
    for table in font["cmap"].tables:
        if ord(glyph) in table.cmap.keys():
            return True
    return False


class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        for MY_GUILD in MY_GUILDS:
            self.tree.copy_global_to(guild=MY_GUILD)
            await self.tree.sync(guild=MY_GUILD)


client = MyClient()


@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("------")


@client.tree.context_menu(name="StickerInfo")
async def stickerinfo(ctx: discord.Interaction, message: discord.Message):
    try:
        if len(message.stickers) == 0:
            await ctx.response.send_message(
                "No sticker in this message", ephemeral=True
            )
            return
        sticker = message.stickers[0]

        embed = discord.Embed(title=sticker.name, url=sticker.url)
        embed.add_field(name="id", value=sticker.id, inline=False)
        embed.set_image(url=sticker.url)
        await ctx.response.send_message(embed=embed)
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        await ctx.response.send_message("Error finding sticker", ephemeral=True)


@client.tree.command(name="banner", description="Get user banner")
@app_commands.describe(user="server member")
async def banner(ctx: discord.Interaction, user: discord.Member):
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


@client.tree.command(name="piechart", description="Creates a pie chart")
@app_commands.describe(
    labels="labels seperated by ,",
    values="chart values seperated by ,",
    title="title of chart",
)
async def piechart(ctx: discord.Interaction, labels: str, values: str, title: str):
    try:
        labelslst = labels.split(",")
        valueslst = values.split(",")
        fig = go.Figure(
            data=[go.Pie(labels=labelslst, values=valueslst, textinfo="none")]
        )
        fig.update_layout(title={"text": title, "x": 0.5})
        img_bytes = fig.to_image(format="png")
        await ctx.response.send_message(
            file=discord.File(
                fp=BytesIO(img_bytes), filename=f"{str(uuid.uuid4())}.png"
            )
        )
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        await ctx.response.send_message("Error creating pie chart")


@client.tree.command(name="apng2gif", description="Convert apng file to gif")
@app_commands.describe(file="apng file", link="direct url to apng file")
async def apng2gif(
    ctx: discord.Interaction, file: Optional[discord.Attachment] = None, link: str = ""
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


@client.tree.command(name="lottie2gif", description="Convert lottie file to gif")
@app_commands.describe(file="lottie file", link="direct url to lottie file")
async def lottie2gif(
    ctx: discord.Interaction, file: Optional[discord.Attachment] = None, link: str = ""
):
    await ctx.response.defer()
    try:
        imagedata = await getimagedata(file, link, "json", ".json")
        error = imagedata.error

        if error != "":
            await ctx.followup.send(error, ephemeral=True)
            return

        imagebytes = imagedata.imagebytes
        filename = imagedata.filename

        with open(filename, "wb") as f:
            f.write(imagebytes)
        # convert to gif
        run(
            convSingleLottie(
                LottieFile(filename), set([str(Path(filename).with_suffix(".gif"))])
            )
        )

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


@client.tree.command(name="spongebob", description="Adds text to spongebob image")
@app_commands.describe(
    text="Text to add to image",
)
async def spongebob(ctx: discord.Interaction, text: str):
    await ctx.response.defer()
    try:
        addstr = str(text)
        img = Image.open("images/spongebob.jpg")
        draw = ImageDraw.Draw(img)
        startlen = 590
        FONT_SIZE = 55
        # loop through and add each character to image
        for char in addstr:
            # check for character in fonts
            checkfont = TTFont("uni.ttf")
            checkfont2 = TTFont("color.ttf")
            if has_glyph(checkfont, char):
                font = ImageFont.truetype("uni.ttf", FONT_SIZE, encoding="unic")
            elif has_glyph(checkfont2, char):
                font = ImageFont.truetype("color.ttf", FONT_SIZE)
            else:
                font = ImageFont.truetype("uni.ttf", FONT_SIZE, encoding="unic")
            size = font.getlength(char)
            # add text to image
            draw.text((startlen, 20), char, font=font, embedded_color=True)
            startlen += int(size)
        # send final image
        with BytesIO() as image_binary:
            img.save(image_binary, "PNG")
            image_binary.seek(0)
            await ctx.followup.send(
                file=discord.File(fp=image_binary, filename="image.png")
            )
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        await ctx.followup.send("Error adding text to image", ephemeral=True)


@client.tree.command(name="giframe", description="Returns random frame from gif")
@app_commands.describe(file="gif file", link="direct url link to gif")
async def giframe(
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

        # read image from url
        gif = Image.open(BytesIO(imgbytes))
        num_frames = gif.n_frames
        # select random frame
        rand_frame = random.randint(0, num_frames - 1)
        gif.seek(rand_frame)
        # send final image
        with BytesIO() as image_binary:
            gif.save(image_binary, "PNG")
            image_binary.seek(0)
            await ctx.followup.send(
                file=discord.File(fp=image_binary, filename=filename)
            )
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        await ctx.followup.send("Error generating random frame", ephemeral=True)


@client.tree.command(name="reversegif", description="Reverses a gif")
@app_commands.describe(file="gif file", link="direct url link to gif")
async def reversegif(
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
        await ctx.followup.send("Error generating random frame", ephemeral=True)


@client.tree.command(name="amogus", description="Creates amogus image")
@app_commands.describe(
    file="image file", link="direct url to image", lines="height of output image"
)
async def amogus(
    ctx: discord.Interaction,
    file: Optional[discord.Attachment] = None,
    link: str = "",
    lines: discord.app_commands.Range[int, 10, 30] = 20,
):
    await ctx.response.defer()
    try:
        imagedata = await getimagedata(file, link, "image", ".gif")
        error = imagedata.error

        if error != "":
            await ctx.followup.send(error, ephemeral=True)
            return
        imagebytes = imagedata.imagebytes
        filename = imagedata.filename

        frames = dumpy(imagebytes, lines)
        frame_one = frames[0]
        with BytesIO() as gif_binary:
            frame_one.save(
                gif_binary,
                format="GIF",
                append_images=frames,
                save_all=True,
                duration=100,
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
        await ctx.followup.send("Error creating amogus gif", ephemeral=True)


@client.tree.command(name="creatememe", description="Create meme from an image")
@app_commands.describe(
    file="image or gif file", text="top and bottom text seperated by ,"
)
async def creatememe(ctx: discord.Interaction, file: discord.Attachment, text: str):
    await ctx.response.defer()
    try:
        if (
            file.content_type is not None
            and file.content_type.startswith("image") == False
        ):
            await ctx.followup.send("file must be an image", ephemeral=True)
            return
        async with aiohttp.ClientSession() as session:

            baseurl = "https://api.memegen.link/images/custom"
            payload = {"background": file.url, "text": text.split(",")}
            async with session.post(url=baseurl, data=payload) as response:
                response = await response.json()
            async with session.get(response["url"]) as resp:
                await ctx.followup.send(
                    file=discord.File(
                        fp=BytesIO(await resp.read()), filename=file.filename
                    )
                )

    except Exception as e:
        print(e)
        print(traceback.format_exc())
        await ctx.followup.send("Error creating meme", ephemeral=True)


class Scroller(discord.ui.View):
    def __init__(
        self,
        responselst,
        embedfunc: Optional[Callable[[Any, int], discord.Embed]] = None,
    ) -> None:
        super().__init__(timeout=20)
        self.count = 0
        self.responselst = responselst
        self.embedfunc = embedfunc

    @discord.ui.button(style=discord.ButtonStyle.gray, emoji="⬅️")
    async def left(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.count = max(0, self.count - 1)
        if self.embedfunc is not None:
            embed = self.embedfunc(self.responselst, self.count)
            await interaction.response.edit_message(embed=embed)
            return
        await interaction.response.edit_message(content=self.responselst[self.count])

    @discord.ui.button(style=discord.ButtonStyle.gray, emoji="➡️")
    async def right(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.count = min(len(self.responselst) - 1, self.count + 1)
        if self.embedfunc is not None:
            embed = self.embedfunc(self.responselst, self.count)
            await interaction.response.edit_message(embed=embed)
            return
        await interaction.response.edit_message(content=self.responselst[self.count])


@client.tree.command(name="memetemplates", description="List image templates")
@app_commands.describe(search="filter meme templates")
async def memetemplates(ctx: discord.Interaction, search: str = ""):
    await ctx.response.defer()
    try:
        baseurl = "https://api.memegen.link/templates"
        if search != "":
            response = requests.get(baseurl, params={"filter": search}).json()
        else:
            response = requests.get(baseurl).json()

        if len(response) == 0:
            await ctx.followup.send("No templates found", ephemeral=True)
            return

        def embedfunc(response, count: int) -> discord.Embed:
            description = (
                f"Use this template by providing the id in /creatememetemplate"
            )
            embed = discord.Embed(
                title=response[count]["name"], description=description
            )
            embed.add_field(name="id", value=response[count]["id"])
            embed.set_image(url=response[count]["blank"])
            return embed

        embed = embedfunc(response, 0)
        view = Scroller(response, embedfunc=embedfunc)
        msg = await ctx.followup.send(embed=embed, view=view)
        timeout = await view.wait()
        if timeout:
            if isinstance(msg, discord.WebhookMessage):
                await msg.edit(view=None)  # type: ignore
            elif isinstance(msg, discord.Interaction):
                await msg.edit_original_response(view=None)  # type: ignore

    except Exception as e:
        print(e)
        print(traceback.format_exc())
        await ctx.followup.send("Error creating meme", ephemeral=True)


@client.tree.command(
    name="creatememetemplate", description="Creates a meme from a template id"
)
@app_commands.describe(id="id of template", text="top and bottom text seperated by ,")
async def creatememetemplate(ctx: discord.Interaction, id: str, text: str):
    await ctx.response.defer()
    try:
        baseurl = f"https://api.memegen.link/templates/{id.strip()}"
        payload = {"text": text.split(",")}
        response = requests.post(baseurl, data=payload).json()
        await ctx.followup.send(response["url"])

    except Exception as e:
        print(e)
        print(traceback.format_exc())
        await ctx.followup.send("Error creating meme", ephemeral=True)


@client.tree.command(
    name="knowyourmeme", description="Searches know your meme for submission"
)
@app_commands.describe(search="name of meme")
async def kym(ctx: discord.Interaction, search: str):
    await ctx.response.defer()
    try:
        url = f'https://knowyourmeme.com/search?q={search.replace(" ","+")}'
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=header)
        soup = BeautifulSoup(resp.content, "html.parser")
        alllinks: List[str] = []
        for link in soup.find_all("a"):
            if (
                "/memes/" in link["href"]
                and link.has_attr("class")
                and link["class"] == ["photo"]
            ):
                alllinks.append(f"https://knowyourmeme.com{link['href']}")
        if len(alllinks) == 0:
            await ctx.followup.send("No results found", ephemeral=True)
            return
        view = Scroller(alllinks)
        msg = await ctx.followup.send(content=alllinks[0], view=view)
        timeout = await view.wait()
        if timeout:
            if isinstance(msg, discord.WebhookMessage):
                await msg.edit(view=None)  # type: ignore
            elif isinstance(msg, discord.Interaction):
                await msg.edit_original_response(view=None)  # type: ignore

    except Exception as e:
        print(e)
        print(traceback.format_exc())
        await ctx.followup.send("Error searching kym", ephemeral=True)


@client.tree.command(name="info", description="Extra info about the bot")
async def info(ctx: discord.Interaction):
    embed = discord.Embed(
        title="MemeBot Info", description="This bot is managed by vision#5160"
    )
    embed.add_field(
        name="💻 Source Code:",
        value="[Click Here](https://github.com/mikytron123/MemeMaker-Discord-bot)",
        inline=False,
    )
    await ctx.response.send_message(embed=embed)


@client.tree.command(name="speechbubble", description="Add speechbubble to image")
@app_commands.describe(file="image file")
async def speechbubble(ctx: discord.Interaction, file: discord.Attachment):
    await ctx.response.defer()
    try:
        if file.content_type is None:
            await ctx.followup.send("Unkown file type", ephemeral=True)
            return
        if "image" not in file.content_type:
            await ctx.followup.send("file must be a image", ephemeral=True)
            return
        bubble = Image.open("images/speechbubble.png")
        response = requests.get(file.url)
        img = Image.open(BytesIO(response.content))

        bubble = bubble.resize((img.size[0], round(img.size[1] / 4)))
        finalwidth = img.size[0]
        finalheight = img.size[1] + bubble.size[1]

        newimg = Image.new("RGB", (finalwidth, finalheight))
        newimg.paste(bubble, (0, 0))
        newimg.paste(img, (0, bubble.size[1]))

        with BytesIO() as image_binary:
            newimg.save(image_binary, "PNG")
            image_binary.seek(0)
            await ctx.followup.send(
                file=discord.File(
                    fp=image_binary,
                    filename=str(Path(file.filename).with_suffix(".png")),
                )
            )

    except Exception as e:
        print(e)
        print(traceback.format_exc())
        await ctx.followup.send("Error adding speechbubble to image", ephemeral=True)


client.run(TOKEN)

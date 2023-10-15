# bot.py
import glob
import traceback
from io import BytesIO
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

import discord
import nest_asyncio
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

from config import read_configs
from dumpy import dumpy
from utils import clean_str, getimagedata, memerequest, parse_cli_args, tenorsearch
from views import EditView, Scroller

load_dotenv()

nest_asyncio.apply()

args = parse_cli_args()

configs = read_configs(prod=args.prod)
TOKEN: str = configs.token
MY_GUILDS: List[discord.Object] = configs.guilds


def has_glyph(font, glyph):
    for table in font["cmap"].tables:
        if ord(glyph) in table.cmap.keys():
            return True
    return False


class MyClient(commands.Bot):
    def __init__(self):
        super().__init__(intents=discord.Intents.default(), command_prefix="$")

    async def setup_hook(self):
        for file in glob.glob("cogs/*.py"):
            await client.load_extension(file.replace("/", ".")[:-3])
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
        # write code for a pie chart using matplotlib
        fig, ax = plt.subplots()
        ax.pie(valueslst)
        plt.title(title)
        plt.legend(labels=labelslst, loc="best", bbox_to_anchor=(1, 0.85))
        filename = f"{clean_str(title)}.png"
        plt.savefig(filename, bbox_inches="tight")

        await ctx.response.send_message(
            file=discord.File(fp=filename, filename=filename)
        )
        filepath = Path(filename)
        filepath.unlink()

    except Exception as e:
        print(e)
        print(traceback.format_exc())
        await ctx.response.send_message("Error creating pie chart")


@client.tree.command(name="spongebobmeme", description="Adds text to spongebob image")
@app_commands.describe(
    text="Text to add to image",
)
async def spongebobmeme(ctx: discord.Interaction, text: str):
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


@client.tree.command(name="sotrue", description="Creates a so true meme")
@app_commands.describe(
    file="image file to add to image",
)
async def sotrue(ctx: discord.Interaction, file: discord.Attachment):
    await ctx.response.defer()
    try:
        if file.content_type is None:
            await ctx.followup.send("Unknown file type", ephemeral=True)

        if "image" not in file.content_type:  # type: ignore
            await ctx.followup.send("file must be a image", ephemeral=True)

        img = Image.open("images/sotrue.png")
        image_bytes = requests.get(file.url).content
        img2 = Image.open(BytesIO(image_bytes))
        img2 = img2.resize((img.size[0] // 2 - 5, img.size[1] // 2 - 5))
        img.paste(img2, (img.size[0] // 2 + 2, img.size[1] // 2 + 2))

        # send final image
        with BytesIO() as image_binary:
            img.save(image_binary, "PNG")
            image_binary.seek(0)
            await ctx.followup.send(
                file=discord.File(fp=image_binary, filename=f"{file.filename}.png")
            )
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        await ctx.followup.send("Error adding text to image", ephemeral=True)


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
    file="image or gif file",
    text="top and bottom text seperated by ,",
    link="direct link to image or gif",
)
async def creatememe(
    ctx: discord.Interaction,
    text: str,
    file: Optional[discord.Attachment] = None,
    link: str = "",
):
    await ctx.response.defer()
    try:
        if (file is None and link == "") or (file is not None and link != ""):
            await ctx.followup.send(
                "Must specify exactly one of file or link argument", ephemeral=True
            )

        if file is not None:
            if file.content_type is None:
                await ctx.followup.send("Unknown file type", ephemeral=True)

            if "image" not in file.content_type:  # type: ignore
                await ctx.followup.send("file must be a image", ephemeral=True)
            url = file.url
            filename = file.filename
        else:
            url = link
            filename = urlparse(link).path.split("/")[-1]
            url_request = requests.head(url)

            if url_request.status_code == 200:
                if "tenor.com" in url:
                    url = await tenorsearch(url)
                    filename = urlparse(url).path.split("/")[-1]
                else:
                    content_type = url_request.headers["Content-Type"]

                    if "image" not in content_type:
                        await ctx.followup.send("file must be a image", ephemeral=True)
            else:
                await ctx.followup.send("Invalid link", ephemereal=True)

        imagebytes = await memerequest(url, text)
        view = EditView(url, filename)
        msg = await ctx.followup.send(
            file=discord.File(fp=BytesIO(imagebytes), filename=filename),
            view=view,
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
        await ctx.followup.send("Error creating meme", ephemeral=True)


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
            description = "Use this template by providing the id in /creatememetemplate"
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
        await ctx.followup.send("Error searching meme templates", ephemeral=True)


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
        url = f'https://knowyourmeme.com/search?q={search.replace(" ", "+")}'
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


@client.tree.command(name="speechbubble", description="Add speechbubble to image")
@app_commands.describe(file="image file", link="direct link to image")
async def speechbubble(
    ctx: discord.Interaction, file: Optional[discord.Attachment] = None, link: str = ""
):
    await ctx.response.defer()
    try:
        imagedata = await getimagedata(file, link, "image", ".png")
        error = imagedata.error

        if error != "":
            await ctx.followup.send(error, ephemeral=True)
            return

        imagebytes = imagedata.imagebytes
        filename = imagedata.filename
        img = Image.open(BytesIO(imagebytes))

        bubble = Image.open("images/speechbubble.png")
        bubble = bubble.resize((img.size[0], round(img.size[1] / 4)))
        finalwidth = img.size[0]
        finalheight = img.size[1] + bubble.size[1]

        newimg = Image.new("RGBA", (finalwidth, finalheight), (255, 255, 255, 0))
        newimg.paste(bubble, (0, 0))
        newimg.paste(img, (0, bubble.size[1]))

        with BytesIO() as image_binary:
            newimg.save(image_binary, "PNG")
            image_binary.seek(0)
            await ctx.followup.send(
                file=discord.File(
                    fp=image_binary,
                    filename=str(Path(filename).with_suffix(".png")),
                )
            )

    except Exception as e:
        print(e)
        print(traceback.format_exc())
        await ctx.followup.send("Error adding speechbubble to image", ephemeral=True)


@client.tree.command(name="grid", description="Create grid of images")
@app_commands.describe(title="title of image", image1="image file")
async def grid(
    ctx: discord.Interaction,
    title: str,
    image1: discord.Attachment,
    image2: Optional[discord.Attachment] = None,
    image3: Optional[discord.Attachment] = None,
    image4: Optional[discord.Attachment] = None,
    image5: Optional[discord.Attachment] = None,
    image6: Optional[discord.Attachment] = None,
    image7: Optional[discord.Attachment] = None,
    image8: Optional[discord.Attachment] = None,
    image9: Optional[discord.Attachment] = None,
):
    await ctx.response.defer()
    try:
        img_width = 300
        img_height = 300
        FONT_SIZE = 30

        imagelst = [
            image1,
            image2,
            image3,
            image4,
            image5,
            image6,
            image7,
            image8,
            image9,
        ]
        imagelst = [x for x in imagelst if x is not None]
        font = ImageFont.truetype("uni.ttf", FONT_SIZE, encoding="unic")

        rows = round(len(imagelst) ** (1 / 2))
        if rows**2 < len(imagelst):
            cols = rows + 1
        else:
            cols = rows

        final_width = img_width * cols
        final_height = img_height * rows + 50

        newimg = Image.new("RGB", (final_width, final_height), color="white")
        draw = ImageDraw.Draw(newimg)
        font = ImageFont.truetype("uni.ttf", FONT_SIZE, encoding="unic")

        draw.text((5, 5), title, font=font, fill=(0, 0, 0))

        for ii, img in enumerate(imagelst):
            grid_img = Image.open(BytesIO(requests.get(img.url).content))
            grid_img = grid_img.resize((img_width, img_height))
            num = str(ii + 1)
            corner = (ii % cols) * img_width, (ii // cols) * img_height + 50
            grid_img_draw = ImageDraw.Draw(grid_img)
            grid_img_draw.text((5, 5), num, font=font, embedded_color=True)
            newimg.paste(grid_img, corner)

        filename = str(Path(clean_str(title)).with_suffix(".png"))
        with BytesIO() as image_binary:
            newimg.save(image_binary, "PNG")
            image_binary.seek(0)
            await ctx.followup.send(
                file=discord.File(
                    fp=image_binary,
                    filename=filename,
                )
            )

    except Exception as e:
        print(e)
        print(traceback.format_exc())
        await ctx.followup.send("Error making grid image", ephemeral=True)


if __name__ == "__main__":
    client.run(TOKEN)

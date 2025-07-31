# bot.py
import glob
import traceback
from io import BytesIO
from pathlib import Path
from typing import List, Optional, cast
import discord
import nest_asyncio
import asyncio
import matplotlib.pyplot as plt
import httpx
from bs4 import BeautifulSoup
from discord import app_commands, Emoji
from discord.ext import commands
from dotenv import load_dotenv
import tempfile
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from config import read_configs, parse_cli_args
from decorators import log_arguments, timer_function
from dumpy import dumpy
from image_handler import FileImage, create_image_class
from utils import clean_str, memerequest
from views import EditView, Scroller

load_dotenv()

nest_asyncio.apply()

args = parse_cli_args()

configs = read_configs(prod=args.prod)
TOKEN: str = configs.token
MY_GUILDS: List[discord.Object] = configs.guilds


class DiscordClient(commands.Bot):
    def __init__(self):
        super().__init__(intents=discord.Intents.default(), command_prefix="$")

    async def setup_hook(self):
        for file in glob.glob("cogs/*.py"):
            await client.load_extension(file.replace("/", ".")[:-3])
        for MY_GUILD in MY_GUILDS:
            self.tree.copy_global_to(guild=MY_GUILD)
            await self.tree.sync(guild=MY_GUILD)


client = DiscordClient()
httpClient = httpx.Client(timeout=120)


@client.event
async def on_ready():
    user = client.user
    if user is not None:
        print(f"Logged in as {user} (ID: {user.id})")
        print("------")


@client.tree.context_menu(name="StickerInfo")
@log_arguments
@timer_function
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


@client.tree.context_menu(name="Its Over")
@log_arguments
@timer_function
async def react_over(ctx: discord.Interaction, message: discord.Message):
    await ctx.response.defer()
    try:
        over_emotes = np.array(
            [
                "Ov1_Dover",
                "Ov2_Ogre",
                "Ov3_Garftover",
                "Ov4_Joever",
                "Ov5_Beyondover",
                "Ov6_Daredover",
                "Ov7_Maxvocadover",
                "Ov8_Kangover",
                "Ov10_noruegover",
                "Ov11_Vidover",
                "Ov12_nikkover",
                "Ov13_lizardkingover",
                "Ov14_Strummer",
                "Ov15_Vertover",
                "Ov16_ileiadover",
                "Ov17_Ryanover",
                "Ov18_SlimLover",
                "Ov19_Krover",
                "Ov20_Bartendover",
                "Ov21_Maddover",
            ]
        )
        current_reactions = message.reactions

        current_over_reactions = np.array(
            list(
                map(
                    lambda y: cast(Emoji, y.emoji).name,
                    filter(
                        lambda x: isinstance(x.emoji, Emoji)
                        and x.emoji.name in over_emotes,
                        current_reactions,
                    ),
                )
            )
        )
        remaining_over_reactions = over_emotes[
            np.isin(over_emotes, current_over_reactions, invert=True)
        ]

        server = ctx.guild
        if server is None:
            await ctx.response.send_message("Missing Server", ephemeral=True)
            return

        server_emotes = tuple(filter(lambda x: x.available, server.emojis))

        available_over_emotes = list(
            filter(lambda x: x.name in remaining_over_reactions, server_emotes)
        )

        emote_limit = 20 - len(current_reactions)
        available_over_emotes = available_over_emotes[-emote_limit:]

        for emote in available_over_emotes:
            await message.add_reaction(emote)
            await asyncio.sleep(1)

        await ctx.followup.send("Reactions added", ephemeral=True)
        await asyncio.sleep(5)
        await ctx.delete_original_response()

    except Exception as e:
        print(e)
        print(traceback.format_exc())
        await ctx.followup.send("Error reacting to message", ephemeral=True)
        await asyncio.sleep(5)
        await ctx.delete_original_response()


@client.tree.command(name="piechart", description="Creates a pie chart")
@app_commands.describe(
    labels="labels seperated by ,",
    values="chart values seperated by ,",
    title="title of chart",
)
@log_arguments
@timer_function
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

        with tempfile.NamedTemporaryFile(suffix=".png") as fp:
            plt.savefig(fp.name, bbox_inches="tight")

            await ctx.response.send_message(
                file=discord.File(fp=fp.name, filename=filename)
            )

    except Exception as e:
        print(e)
        print(traceback.format_exc())
        await ctx.response.send_message("Error creating pie chart")


@client.tree.command(name="sotrue", description="Creates a so true meme")
@app_commands.describe(
    file="image file to add to image",
)
@log_arguments
@timer_function
async def sotrue(ctx: discord.Interaction, file: discord.Attachment):
    await ctx.response.defer()
    try:
        file_img = FileImage(file=file, filetype="image")
        image_bytes = await file_img.get_image_bytes()
        filename = str(Path(file_img.get_filename()).with_suffix(".png"))

        img = Image.open("images/sotrue.png")

        img2 = Image.open(BytesIO(image_bytes))
        img2 = img2.resize((img.size[0] // 2 - 5, img.size[1] // 2 - 5))
        img.paste(img2, (img.size[0] // 2 + 2, img.size[1] // 2 + 2))

        # send final image
        with BytesIO() as image_binary:
            img.save(image_binary, "PNG")
            image_binary.seek(0)
            await ctx.followup.send(
                file=discord.File(fp=image_binary, filename=filename)
            )
    except ValueError as v:
        print(v)
        await ctx.followup.send(str(v), ephemeral=True)
        return
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        await ctx.followup.send("Error adding text to image", ephemeral=True)


@client.tree.command(name="amogus", description="Creates amogus image")
@app_commands.describe(
    file="image file", link="direct url to image", lines="height of output image"
)
@log_arguments
@timer_function
async def amogus(
    ctx: discord.Interaction,
    file: Optional[discord.Attachment] = None,
    link: str = "",
    lines: discord.app_commands.Range[int, 10, 30] = 20,
):
    await ctx.response.defer()
    try:
        img = await create_image_class(file, link, "image")
        imagebytes = await img.get_image_bytes()
        filename = str(Path(img.get_filename()).with_suffix(".gif"))

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
            await ctx.followup.send(file=discord.File(fp=gif_binary, filename=filename))
    except ValueError as v:
        print(v)
        await ctx.followup.send(str(v), ephemeral=True)
        return

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
@log_arguments
@timer_function
async def creatememe(
    ctx: discord.Interaction,
    text: str,
    file: Optional[discord.Attachment] = None,
    link: str = "",
):
    await ctx.response.defer()
    try:
        img = await create_image_class(file, link, "image")
        url = img.get_url()
        filename = img.get_filename()

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

    except ValueError as v:
        print(v)
        await ctx.followup.send(str(v), ephemeral=True)
        return

    except Exception as e:
        print(e)
        print(traceback.format_exc())
        await ctx.followup.send("Error creating meme", ephemeral=True)


@client.tree.command(name="memetemplates", description="List image templates")
@app_commands.describe(search="filter meme templates")
@log_arguments
@timer_function
async def memetemplates(ctx: discord.Interaction, search: str = ""):
    await ctx.response.defer()
    try:
        baseurl = "https://api.memegen.link/templates"
        if search != "":
            response = (httpClient.get(baseurl, params={"filter": search})).json()
        else:
            response = (httpClient.get(baseurl)).json()

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
@log_arguments
@timer_function
async def creatememetemplate(ctx: discord.Interaction, id: str, text: str):
    await ctx.response.defer()
    try:
        baseurl = f"https://api.memegen.link/templates/{id.strip()}"
        payload = {"text": text.split(",")}

        response = (httpClient.post(baseurl, data=payload)).json()
        await ctx.followup.send(response["url"])

    except Exception as e:
        print(e)
        print(traceback.format_exc())
        await ctx.followup.send("Error creating meme", ephemeral=True)


@client.tree.command(
    name="knowyourmeme", description="Searches know your meme for submission"
)
@app_commands.describe(search="name of meme")
@log_arguments
@timer_function
async def kym(ctx: discord.Interaction, search: str):
    await ctx.response.defer()
    try:
        url = f"https://knowyourmeme.com/search?q={search.replace(' ', '+')}"
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36"
        }

        resp = httpClient.get(url, headers=header)
        soup = BeautifulSoup(resp.content, "html.parser")
        all_links: list[str] = []
        for link in soup.find_all("a"):
            href_val = link.get("href", "")
            if (
                "/memes/" in href_val
                and len(href_val.split("/")) == 3
                and "=" not in href_val
                and link.get("class", "") == ["item"]
            ):
                all_links.append(f"https://knowyourmeme.com{href_val}")

        all_links = list(dict.fromkeys(all_links))

        if len(all_links) == 0:
            await ctx.followup.send("No results found", ephemeral=True)
            return

        view = Scroller(all_links)
        msg = await ctx.followup.send(content=list(all_links)[0], view=view)
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


@client.tree.command(name="birthday", description="Creates a birthday image")
@app_commands.describe(text="name of user")
@log_arguments
@timer_function
async def bday(ctx: discord.Interaction, text: str):
    await ctx.response.defer()
    try:
        image_path = "images/Laser.jpg"
        font_path = "uni.ttf"
        angle = 35
        img = Image.open(image_path).convert("RGBA")
        font_size = 35

        # Load font
        try:
            if font_path:
                font = ImageFont.truetype(font_path, font_size)
            else:
                font = ImageFont.load_default()
        except IOError:
            print(f"Warning: Could not load font from {font_path}. Using default font.")
            font = ImageFont.load_default()

        text_width = 20 * len(text)
        text_height = 30
        # Get font size
        for font_size in range(35, 15, -1):
            font = ImageFont.truetype(font_path, font_size)
            # get bounding box
            bbox = font.getbbox(text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            if text_width <= 145:
                break

        # create a blank image for text
        x_size = text_width + 5
        y_size = text_height + 20
        txt_img = Image.new("RGBA", (x_size, y_size))
        d = ImageDraw.Draw(txt_img)

        # Draw text on the blank image
        # Position the text at the center of the temporary image
        # text_x = (x_size - text_width) / 2
        # text_y = (y_size - text_height) / 2
        d.text((0, 0), text, font=font, fill="black")

        # Rotate the text image
        rotated_txt_img = txt_img.rotate(
            angle, expand=1, resample=Image.Resampling.BILINEAR
        )

        # bottom left coord
        bl_coord = (-8, img.size[1] - 35)
        # top left coord
        tl_coord = (bl_coord[0], bl_coord[1] - rotated_txt_img.size[1])

        img.paste(rotated_txt_img, tl_coord, rotated_txt_img)
        with BytesIO() as image_binary:
            img.save(image_binary, "PNG")
            image_binary.seek(0)
            await ctx.followup.send(
                file=discord.File(
                    fp=image_binary,
                    filename=f"{clean_str(text)}.png",
                )
            )
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        await ctx.followup.send("Error creating birthday image",ephemeral=True)


@client.tree.command(name="grid", description="Create grid of images")
@app_commands.describe(title="title of image", image1="image file")
@log_arguments
@timer_function
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
        imagelst_filtered = [x for x in imagelst if x is not None]

        rows = round(len(imagelst_filtered) ** (1 / 2))
        if rows**2 < len(imagelst_filtered):
            cols = rows + 1
        else:
            cols = rows

        final_width = img_width * cols
        final_height = img_height * rows + 50

        newimg = Image.new("RGB", (final_width, final_height), color="white")  # type: ignore
        draw = ImageDraw.Draw(newimg)
        font = ImageFont.truetype("uni.ttf", FONT_SIZE, encoding="unic")

        draw.text((5, 5), title, font=font, fill=(0, 0, 0))

        for ii, img in enumerate(imagelst_filtered):
            grid_img = Image.open(BytesIO(httpx.get(img.url).content))
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

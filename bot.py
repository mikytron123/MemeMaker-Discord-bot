# bot.py
import os
import random
from io import BytesIO

import discord
import requests
from discord import app_commands
from dotenv import load_dotenv
from fontTools.ttLib import TTFont
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from dumpy import dumpy

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
if TOKEN is None:
    raise Exception("TOKEN must be set")

def has_glyph(font, glyph):
    for table in font['cmap'].tables:
        if ord(glyph) in table.cmap.keys():
            return True
    return False

MY_GUILD = discord.Object(id=0)  

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

client = MyClient()


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')


@client.tree.command(name="spongebob",description="Adds text to spongebob image")
@app_commands.describe(text="Text to add to image",)
async def spongebob(ctx:discord.Interaction,text:str):
    await ctx.response.defer()
    try:
        addstr = str(text)
        img = Image.open("spongebob.jpg")
        draw = ImageDraw.Draw(img)
        startlen = 590
        FONT_SIZE = 55
        for char in addstr:
            checkfont = TTFont('uni.ttf')
            checkfont2 = TTFont('color.ttf')
            if has_glyph(checkfont,char):
                font = ImageFont.truetype("uni.ttf",FONT_SIZE,encoding='unic')
            elif has_glyph(checkfont2,char):
                font = ImageFont.truetype("color.ttf",FONT_SIZE)
            else:
                font = ImageFont.truetype("uni.ttf",FONT_SIZE,encoding='unic')
            size = font.getsize(char)
            draw.text((startlen, 20),char,font=font,embedded_color=True)
            startlen += size[0]
        with BytesIO() as image_binary:
                img.save(image_binary, 'PNG')
                image_binary.seek(0)
                
                await ctx.followup.send(file=discord.File(fp=image_binary, filename='image.png'))
    except Exception as e:
        print(e)
        await ctx.followup.send("error")

@client.tree.command(name="framegif",description="Returns random frame from gif")
@app_commands.describe(file="gif file",)
async def framegif(ctx:discord.Interaction,file:discord.Attachment):
    print(file.content_type)
    print(file.filename)
    if ("gif" not in file.content_type):
        await ctx.response.send_message("file must be a gif")
        return
    await ctx.response.defer(ephemeral=False)
    response = requests.get(file.url)
    gif = Image.open(BytesIO(response.content))
    num_frames = gif.n_frames
    rand_frame = random.randint(0,num_frames)
    gif.seek(rand_frame)
    with BytesIO() as image_binary:
        gif.save(image_binary, 'PNG')
        image_binary.seek(0)
        await ctx.followup.send(file=discord.File(fp=image_binary, filename='image.png'),ephemeral=False)

@client.tree.command(name="amogus",description="Creates amogus image")
@app_commands.describe(file="image file")
async def amogus(ctx:discord.Interaction,file:discord.Attachment):
    if file.content_type is not None and file.content_type.startswith("image") == False:
        await ctx.response.send_message("file must be an image")
    await ctx.response.defer()
    frames = dumpy(file)
    frame_one = frames[0]
    with BytesIO() as gif_binary:
        frame_one.save(gif_binary,format="GIF",append_images=frames,save_all=True,duration=100,loop=0)
        gif_binary.seek(0)
        await ctx.followup.send(file=discord.File(fp=gif_binary,filename=str(Path(file.filename).with_suffix(".gif"))))
    

client.run(TOKEN)

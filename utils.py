from io import BytesIO
import discord
import requests
from pathlib import Path
from urllib.parse import urlparse
from typing import NamedTuple,Optional
import os
import aiohttp
from PIL import Image
import random
import argparse

def parse_cli_args():
    parser = argparse.ArgumentParser(
                    prog='MemeBot',
                    description='Discord Bot')
    parser.add_argument("--prod",
                        action="store_true",
                        default=False
                        )
    
    return parser.parse_args()



class Imagedata(NamedTuple):
    imagebytes: bytes
    filename: str
    error: str = ""  

async def getimagedata(file:Optional[discord.Attachment],
                       link:str,
                       filetype:str,
                       suffix:str) -> Imagedata:
    
    if (file is None and link == "") or (file is not None and link != ""):
        return Imagedata(b'',"","Must specify exactly one of file or link argument")
    
    if file is not None:
    
        if file.content_type is None:
            return Imagedata(b'',"","Unknown file type")
    
        if filetype not in file.content_type:
            return Imagedata(b'',"",f"file must be a {filetype}")
    
        url = file.url
        response = requests.get(url)
        imgbytes = response.content
        filename = str(Path(file.filename).with_suffix(suffix))
        return Imagedata(imgbytes,filename)
    
    else:
        if filetype=="gif" and "tenor.com" in link:
            if link.endswith(".mp4") or link.endswith(".webm"):
                return Imagedata(b'',"","link must redirect to a gif")
            link = await tenorsearch(link)
            if link=="error":
                return Imagedata(b'',"","error finding gif on tenor, use direct gif instead")

        response = requests.get(link)
        if response.status_code<200 or response.status_code>300:
            return Imagedata(b'',"","Invalid url")
        content_type = response.headers["Content-Type"]
    
        if filetype not in content_type:
            return Imagedata(b'',"",f"link must redirect to a {filetype}")
    
        imgbytes = response.content
        filename = str(Path(urlparse(link).path.split("/")[-1]).with_suffix(suffix))
        return Imagedata(imgbytes,filename,"")
    
async def tenorsearch(url:str)->str:
    # set the apikey and limit
    apikey = os.getenv("TENOR_TOKEN")
    ckey = "MemeBot"
    id = url.split("-")[-1]

    r = requests.get(
        "https://tenor.googleapis.com/v2/posts",
        params={"key":apikey,
                "ids":id,
                "client_key":ckey,
                "media_filter":"gif"}
        )

    if r.status_code == 200:
        # load the GIFs using the urls for the smaller GIF sizes
        response = r.json()
        tenor_url = response["results"][0]["media_formats"]["gif"]["url"]
        return tenor_url
    else:
        return "error"

async def memerequest(background: str, text: str) -> bytes:
    baseurl = "https://api.memegen.link/images/custom"
    payload = {"background": background, "text": text.split(",")}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=baseurl, data=payload) as response:
            response = await response.json()
        async with session.get(response["url"]) as resp:
            imagebytes = await resp.read()
            return imagebytes

async def seekrandomframe(imgbytes:bytes)->BytesIO:
    gif = Image.open(BytesIO(imgbytes))
    num_frames = gif.n_frames
    # select random frame
    rand_frame = random.randint(0, num_frames - 1)
    gif.seek(rand_frame)
    # send final image
    image_binary = BytesIO()
    gif.save(image_binary, "PNG")
    image_binary.seek(0)
    return image_binary
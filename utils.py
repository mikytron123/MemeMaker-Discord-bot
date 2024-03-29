from io import BytesIO
import discord
import requests
from pathlib import Path
from urllib.parse import urlparse
from typing import NamedTuple, Optional
import os
import aiohttp
from PIL import Image
import random


class Imagedata(NamedTuple):
    imagebytes: bytes
    filename: str
    error: str = ""


async def getimagedata(
    file: Optional[discord.Attachment], link: str, filetype: str, suffix: str
) -> Imagedata:
    if (file is None and link == "") or (file is not None and link != ""):
        return Imagedata(b"", "", "Must specify exactly one of file or link argument")

    if file is not None:
        if file.content_type is None:
            return Imagedata(b"", "", "Unknown file type")

        if filetype not in file.content_type:
            return Imagedata(b"", "", f"file must be a {filetype}")

        url = file.url
        response = requests.get(url)
        imgbytes = response.content
        filename = str(Path(file.filename).with_suffix(suffix))
        return Imagedata(imgbytes, filename)

    else:
        if filetype == "gif" and "tenor.com" in link:
            if link.endswith(".mp4") or link.endswith(".webm"):
                return Imagedata(b"", "", "link must redirect to a gif")
            link = await tenorsearch(link)
            if link is None:
                return Imagedata(
                    b"", "", "error finding gif on tenor, use direct gif instead"
                )

        response = requests.get(link)
        if response.status_code < 200 or response.status_code > 300:
            return Imagedata(b"", "", "Invalid url")
        content_type = response.headers["Content-Type"]

        if filetype not in content_type:
            return Imagedata(b"", "", f"link must redirect to a {filetype}")

        imgbytes = response.content
        filename = str(Path(urlparse(link).path.split("/")[-1]).with_suffix(suffix))
        return Imagedata(imgbytes, filename, "")


async def tenorsearch(url: str) -> Optional[str]:
    # set the apikey and limit
    apikey = os.getenv("TENOR_TOKEN")
    if apikey is None:
        return
    ckey = "MemeBot"
    id = url.split("-")[-1]

    r = requests.get(
        "https://tenor.googleapis.com/v2/posts",
        params={"key": apikey, "ids": id, "client_key": ckey, "media_filter": "gif"},
    )

    if r.status_code == 200:
        # load the GIFs using the urls for the smaller GIF sizes
        response = r.json()
        tenor_url = response["results"][0]["media_formats"]["gif"]["url"]
        return tenor_url
    else:
        return


async def memerequest(background: str, text: str) -> bytes:
    baseurl = "https://api.memegen.link/images/custom"
    text = list(map(lambda x: x.strip(), text.split(",")))
    payload = {"background": background, "text": text}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=baseurl, data=payload) as response:
            response = await response.json()
            meme_url = response["url"]
            # only bottom text case
            if text[0] == "":
                meme_text = urlparse(meme_url).path.split("/")[-1]
                meme_url = meme_url.replace(meme_text, f"_/{meme_text}")

        async with session.get(meme_url) as resp:
            return await resp.read()


def seekrandomframe(imgbytes: bytes) -> BytesIO:
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


def clean_str(filename: str) -> str:
    filename_clean = filename.replace(" ", "_")
    return "".join(filter(str.isalnum, filename_clean))

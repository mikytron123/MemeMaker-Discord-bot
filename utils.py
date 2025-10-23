from io import BytesIO
import re
from urllib.parse import urljoin, urlparse
from PIL import Image
import random
from bs4 import BeautifulSoup
import httpx


async def memerequest(background: str, text: str) -> bytes:
    """Sends a request to the meme generation API and returns the image bytes.

    Args:
        background (str): The background image URL or identifier.
        text (str): The text to overlay on the meme, separated by commas for multiple lines

    Returns:
        bytes: The generated meme image in bytes.
    """
    baseurl = "https://api.memegen.link/images/custom"
    payload_text = list(map(lambda x: x.strip(), text.split(",")))
    payload = {"background": background, "text": payload_text}

    async with httpx.AsyncClient() as client:
        req = await client.post(url=baseurl, data=payload)
        response = req.json()
        meme_url = response["url"]
        # only bottom text case
        if payload_text[0] == "":
            meme_text = urlparse(meme_url).path.split("/")[-1]
            meme_url = meme_url.replace(meme_text, f"_/{meme_text}")

        resp = await client.get(meme_url)
        return resp.content


def seekrandomframe(imgbytes: bytes) -> BytesIO:
    """Selects a random frame from a GIF image and returns it as a PNG in a BytesIO object.
    Args:
        imgbytes (bytes): The bytes of the GIF image.
    Returns:
        BytesIO: A BytesIO object containing the PNG image of the selected frame."""
    gif = Image.open(BytesIO(imgbytes))
    num_frames = getattr(gif, "n_frames", 1)
    # select random frame
    rand_frame = random.randint(0, num_frames - 1)
    gif.seek(rand_frame)
    # send final image
    image_binary = BytesIO()
    gif.save(image_binary, "PNG")
    image_binary.seek(0)
    return image_binary


def clean_str(filename: str) -> str:
    """Cleans a string so that it can be used as a filename."""
    filename_clean = filename.replace(" ", "_")
    return "".join(filter(str.isalnum, filename_clean))

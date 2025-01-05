from io import BytesIO
from urllib.parse import urlparse
from PIL import Image
import random
import httpx


async def memerequest(background: str, text: str) -> bytes:
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
    filename_clean = filename.replace(" ", "_")
    return "".join(filter(str.isalnum, filename_clean))

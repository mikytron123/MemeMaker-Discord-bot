from attrs import define, field
import os
import discord
import httpx
import msgspec
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional
from abc import ABC

from datetime import datetime

class DownsizedSmall(msgspec.Struct):
    height: str
    width: str
    mp4_size: str
    mp4: str


class GiphyImage(msgspec.Struct):
    height: str
    width: str
    size: str
    url: str


class Images(msgspec.Struct):
    downsized_medium: GiphyImage


class Data(msgspec.Struct):
    type: str
    id: str
    url: str
    slug: str
    bitly_gif_url: str
    bitly_url: str
    embed_url: str
    username: str
    source: str
    title: str
    rating: str
    content_url: str
    source_tld: str
    source_post_url: str
    is_sticker: int
    import_datetime: datetime
    trending_datetime: datetime
    images: Images


class Meta(msgspec.Struct):
    status: int
    msg: str
    response_id: str


class GiphyAPIResponse(msgspec.Struct):
    data: Data
    meta: Meta


@define
class DiscordImage(ABC):
    filetype: str
    url: str = field(init=False)
    filename: str = field(init=False)

    async def get_image_bytes(self) -> bytes:
        async with httpx.AsyncClient() as client:
            response = await client.get(self.url)

        imgbytes = response.content
        return imgbytes

    def get_filename(self) -> str:
        return self.filename

    def get_url(self) -> str:
        return self.url


@define
class FileImage(DiscordImage):
    file: discord.Attachment = field()

    @file.validator
    def _check_file(self, attribute, value: discord.Attachment):
        if value.content_type is None:
            raise ValueError("Unknown file type")
        elif self.filetype not in value.content_type:
            raise ValueError(f"file must be a {self.filetype}")

    def __attrs_post_init__(self):
        self.url = self.file.url
        self.filename = self.file.filename


@define
class UrlImage(DiscordImage):
    link: str = field()

    @link.validator
    def _check_link(self, attribute, value: str):
        response = httpx.head(value)

        if response.status_code < 200 or response.status_code > 300:
            raise ValueError("Invalid url, returned non 200 status code")

        content_type = response.headers["Content-Type"]

        if self.filetype not in content_type:
            raise ValueError(f"link must redirect to a {self.filetype}")

    def __attrs_post_init__(self):
        self.url = self.link
        self.filename = str(Path(urlparse(self.link).path.split("/")[-1]))


async def create_image_class(
    file: Optional[discord.Attachment], link: str, filetype: str
) -> DiscordImage:
    """Constructs a DiscordImage class based on file or link input."""

    # validate exactly one argument is provided
    if (file is None and link == "") or (file is not None and link != ""):
        raise ValueError("Must specify exactly one of file or link argument")

    if file is not None:
        return FileImage(file=file, filetype=filetype)
    else:
        # handle giphy links
        if "giphy.com/gifs" in link:
            link = await giphysearch(link)
        # handle tenor links
        elif "media1.tenor.com" in link:
            tenor_id = link.split("/")[-2]
            link = f"https://c.tenor.com/{tenor_id}/tenor.gif"
        if "tenor.com" in link:
            if link.endswith(".mp4") or link.endswith(".webm"):
                raise ValueError("link must redirect to a gif")

        return UrlImage(link=link, filetype=filetype)


async def giphysearch(url: str) -> str:
    """Searches for a gif using giphy api"""
    api_key = os.getenv("GIPHY_API_KEY")

    if api_key is None:
        print("GIPHY_API_KEY is not set")
        raise ValueError("GIPHY api key is missing")

    gif_id = url.split("-")[-1]
    params = {"api_key": api_key}

    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://api.giphy.com/v1/gifs/{gif_id}", params=params)

    if r.status_code == 200:
        decoder = msgspec.json.Decoder(type=GiphyAPIResponse)
        # load the GIFs using the urls for the medium GIF sizes
        response = decoder.decode(r.content)
        giphy_url = response.data.images.downsized_medium.url
        return giphy_url

    else:
        raise ValueError("Non 200 status code for giphy api")

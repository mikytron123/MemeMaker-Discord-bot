import os
from abc import ABC
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import discord
import httpx2
import msgspec
from attrs import define, field


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


class Gif(msgspec.Struct):
    url: str
    width: int
    height: int
    size: int


class Hd(msgspec.Struct):
    gif: Gif


class Md(msgspec.Struct):
    gif: Gif


class Sm(msgspec.Struct):
    gif: Gif


class Xs(msgspec.Struct):
    gif: Gif


class File(msgspec.Struct):
    hd: Hd
    md: Md
    sm: Sm
    xs: Xs


class GifItem(msgspec.Struct):
    """A single gif result."""

    id: int
    slug: str
    title: str
    file: File
    tags: list[str]
    type: str
    blur_preview: str


class MetaPayload(msgspec.Struct):
    item_min_width: int
    ad_max_resize_percent: int


class DataPayload(msgspec.Struct):
    data: list[GifItem]
    current_page: int
    per_page: int
    has_next: bool
    meta: MetaPayload


class KlipyApiResponse(msgspec.Struct):
    result: bool
    data: DataPayload


@define
class DiscordImage(ABC):
    filetype: str
    url: str = field(init=False)
    filename: str = field(init=False)

    async def get_image_bytes(self) -> bytes:
        async with httpx2.AsyncClient() as client:
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
        response = httpx2.head(value)

        if response.status_code < 200 or response.status_code > 300:
            raise ValueError("Invalid url, returned non 200 status code")

        content_type = response.headers["Content-Type"]

        if self.filetype not in content_type:
            raise ValueError(f"link must redirect to a {self.filetype}")

    def __attrs_post_init__(self):
        self.url: str = self.link
        self.filename: str = str(Path(urlparse(self.link).path.split("/")[-1]))


async def create_image_class(
    file: discord.Attachment | None, link: str, filetype: str
) -> DiscordImage:
    """Constructs a DiscordImage class based on file or link input."""

    # validate exactly one argument is provided
    if (file is None and link == "") or (file is not None and link != ""):
        raise ValueError("Must specify exactly one of file or link argument")

    if file is not None:
        return FileImage(file=file, filetype=filetype)
    else:
        # handle klipy links
        if "klipy.com/gifs" in link:
            link = await klipysearch(link)
        # handle giphy links
        elif "giphy.com/gifs" in link:
            link = await giphysearch(link)
        # handle tenor links
        elif "media1.tenor.com" in link:
            tenor_id = link.split("/")[-2]
            link = f"https://c.tenor.com/{tenor_id}/tenor.gif"
        if "tenor.com" in link and (link.endswith(".mp4") or link.endswith(".webm")):
            raise ValueError("link must redirect to a gif")

        return UrlImage(link=link, filetype=filetype)


async def klipysearch(url: str) -> str:
    """Searches for a gif using klipy api"""
    api_key = os.getenv("KLIPY_API_KEY")

    if api_key is None:
        print("KLIPY_API_KEY is not set")
        raise ValueError("KLIPY api key is missing")
    gif_slug = url.split("/")[-1]
    customer_id = "memebot"
    url = f"https://api.klipy.com/api/v1/{api_key}/gifs/search"

    params = {
        "page": 1,
        "per_page": 24,
        "q": gif_slug,
        "customer_id": customer_id,
        "format_filter": "gif",
    }
    headers = {"Content-Type": "application/json"}

    response = httpx2.get(url, headers=headers, params=params)
    if response.status_code == 200:
        decoder = msgspec.json.Decoder(type=KlipyApiResponse)
        # load the GIFs using the urls for the medium GIF sizes
        response = decoder.decode(response.content)
        klipy_url = ""
        for gifitem in response.data.data:
            if gifitem.slug.casefold().startswith(gif_slug.casefold()):
                klipy_url = gifitem.file.md.gif.url

        if klipy_url != "":
            return klipy_url
        else:
            raise ValueError("Klipy gif not found")

    else:
        raise ValueError("Non 200 status code for klipy api")


async def giphysearch(url: str) -> str:
    """Searches for a gif using giphy api"""
    api_key = os.getenv("GIPHY_API_KEY")

    if api_key is None:
        print("GIPHY_API_KEY is not set")
        raise ValueError("GIPHY api key is missing")

    gif_id = url.split("-")[-1]
    params = {"api_key": api_key}

    async with httpx2.AsyncClient() as client:
        r = await client.get(f"https://api.giphy.com/v1/gifs/{gif_id}", params=params)

    if r.status_code == 200:
        decoder = msgspec.json.Decoder(type=GiphyAPIResponse)
        # load the GIFs using the urls for the medium GIF sizes
        response = decoder.decode(r.content)
        giphy_url = response.data.images.downsized_medium.url
        return giphy_url

    else:
        raise ValueError("Non 200 status code for giphy api")

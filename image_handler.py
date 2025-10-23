from attrs import define, field
import discord
import httpx
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional
import os
import msgspec
from abc import ABC


class Media(msgspec.Struct):
    url: str


class Response(msgspec.Struct):
    media_formats: dict[str, Media]


class TenorAPIResponse(msgspec.Struct):
    results: list[Response]


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
        # handle tenor links
        if "tenor.com" in link:
            if link.endswith(".mp4") or link.endswith(".webm"):
                raise ValueError("link must redirect to a gif")
            tenor_link = await tenorsearch(link)
            link = tenor_link

        return UrlImage(link=link, filetype=filetype)


async def tenorsearch(url: str) -> str:
    """Searches for gif using tenor API"""
    # set the apikey and limit
    apikey = os.getenv("TENOR_TOKEN")
    if apikey is None:
        print("Tenor API key is not set")
        raise ValueError("tenor API key missing")

    ckey = "MemeBot"
    id = url.split("-")[-1]

    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://tenor.googleapis.com/v2/posts",
            params={
                "key": apikey,
                "ids": id,
                "client_key": ckey,
                "media_filter": "gif",
            },
        )

    if r.status_code == 200:
        decoder = msgspec.json.Decoder(type=TenorAPIResponse)
        # load the GIFs using the urls for the smaller GIF sizes
        # response = r.json()
        response = decoder.decode(r.content)
        tenor_url = response.results[0].media_formats["gif"].url
        return tenor_url
    else:
        raise ValueError("Non 200 status code for tenor api")

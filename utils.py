import discord
import requests
from pathlib import Path
from urllib.parse import urlparse
from collections import namedtuple
from typing import NamedTuple,Optional
import os

class Imagedata(NamedTuple):
    imagebytes: bytes
    filename: str
    error: str = ""  

async def getimagedata(file:Optional[discord.Attachment],link:str,filetype:str,suffix:str) -> Imagedata:
    
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
        if filetype=="gif":
            if "tenor.com" in link:
                if link.endswith(".mp4") or link.endswith(".webm"):
                    return Imagedata(b'',"","link must redirect to a gif")
                link = await tenorsearch(link)
        response = requests.get(link)
        if response.status_code<200 or response.status_code>300:
            return Imagedata(b'',"",f"Invalid url")
        content_type = response.headers["Content-Type"]
    
        if filetype not in content_type:
            return Imagedata(b'',"",f"link must redirect to a {filetype}")
    
        imgbytes = response.content
        filename = str(Path(urlparse(link).path.split("/")[-1]).with_suffix(suffix))
        return Imagedata(imgbytes,filename,"")
    
async def tenorsearch(url:str)->str:
    # set the apikey and limit
    apikey = os.getenv("TENOR_TOKEN")
    lmt = 2
    ckey = "MemeBot"  # set the client_key for the integration and use the same value for all API calls
    search_term = "+".join(urlparse(url).path.split("/")[-1].split("-")[:-1])
    # get the top 8 GIFs for the search term
    r = requests.get(
        "https://tenor.googleapis.com/v2/search",
        params={"key":apikey,
                "q":search_term,
                "client_key":ckey,
                "media_filter":"mediumgif",
                "limit":lmt}
        )

    if r.status_code == 200:
        # load the GIFs using the urls for the smaller GIF sizes
        response = r.json()
        tenor_url = response["results"][0]["media_formats"]["mediumgif"]["url"]
        return tenor_url
    else:
        print(r.content)
        return "error"
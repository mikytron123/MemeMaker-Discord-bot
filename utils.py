import discord
import requests
from pathlib import Path
from urllib.parse import urlparse
from collections import namedtuple
from typing import NamedTuple,Optional


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
        response = requests.get(link)
        content_type = response.headers["Content-Type"]
    
        if filetype not in content_type:
            return Imagedata(b'',"",f"link must redirect to a {filetype}")
    
        imgbytes = response.content
        filename = str(Path(urlparse(link).path.split("/")[-1]).with_suffix(suffix))
        return Imagedata(imgbytes,filename,"")
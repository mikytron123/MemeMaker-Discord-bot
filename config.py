import configparser
import ast
from typing import List,NamedTuple
import discord

class Configuration(NamedTuple):
    token: str
    guilds: List[discord.Object]

def read_configs(dev: bool = False) -> Configuration:
    conf = configparser.ConfigParser()
    if dev:
        print("using dev config")
        configfile = "config-dev.ini"
    else:
        print("using prod config")
        configfile = "config.ini"
    conf.read(configfile)
    TOKEN = conf["DISCORD"]["token"]
    guild_list: List[int] = ast.literal_eval(conf["DISCORD"]["guilds"])
    MY_GUILDS = [discord.Object(id=guild) for guild in guild_list]
    return Configuration(token=TOKEN,guilds=MY_GUILDS)


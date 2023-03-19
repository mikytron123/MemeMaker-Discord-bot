import configparser
import ast
from typing import List, TypedDict
import discord
from collections import namedtuple

configuration = namedtuple("config","token guilds")

def read_configs(dev: bool = False) -> configuration:
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
    return configuration(token=TOKEN,guilds=MY_GUILDS)


import argparse
import configparser
import ast
from typing import List, NamedTuple
import discord


class Configuration(NamedTuple):
    token: str
    guilds: List[discord.Object]


def read_configs(prod: bool) -> Configuration:
    conf = configparser.ConfigParser()
    if not prod:
        print("using dev config")
        configfile = "config-dev.ini"
    else:
        print("using prod config")
        configfile = "config.ini"
    conf.read(configfile)
    TOKEN = conf["DISCORD"]["token"]
    guild_list: List[int] = ast.literal_eval(conf["DISCORD"]["guilds"])
    MY_GUILDS = [discord.Object(id=guild) for guild in guild_list]
    return Configuration(token=TOKEN, guilds=MY_GUILDS)


def parse_cli_args():
    parser = argparse.ArgumentParser(prog="MemeBot", description="Discord Bot")
    parser.add_argument("--prod", action="store_true", default=False)

    return parser.parse_args()

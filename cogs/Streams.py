import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import Button, View
import asyncio
import logging
import math
import time

from utils.ParseJson import ParseJson
from utils.DBUtils import DBUtils
from utils.MsgUtils import MsgUtils
ParseJson = ParseJson()
DBUtils = DBUtils()
MsgUtils = MsgUtils()

config = ParseJson.read_file("config.json")
pokemon_list = ParseJson.read_file("pokemon_list.json")
move_list = ParseJson.read_file("moves.json")

logging.basicConfig(level="WARNING")

class Streams(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cache = {}
        self.weather_cache = {}
        self.clear_time = 0
        self.clear_time_weather = 0
        self.streamer.start()

    def clear_cache(self):
        timestamp = time.time()
        if timestamp >= self.clear_time:
            self.cache = {}
            self.clear_time = timestamp+600

    def clear_weather_cache(self):
        timestamp = time.time()
        if timestamp >= self.clear_time_weather:
            self.weather_cache = {}
            self.clear_time_weather = timestamp+600

    @tasks.loop(seconds=600)
    async def streamer(self):
        self.clear_cache()
        self.clear_weather_cache()

        streams = ParseJson.read_file("streams.json")
        pogo_users = ParseJson.read_file("pogo_users.json")

        GLOBAL_LIMIT = 300 
        stream_length = len(streams)
        if stream_length < 1:
            stream_limit = 0
        else:
            stream_limit = math.floor(GLOBAL_LIMIT/stream_length)

        if stream_limit < 1:
            logging.warning("Msg limit too low. Not enough messages for 1 msg/stream.")
            return

        for channel_id in streams:
            if channel_id not in self.cache.keys():
                self.cache[channel_id] = []
            if channel_id not in self.weather_cache.keys():
                self.weather_cache[channel_id] = []

            params = streams[channel_id]
            pokemon_list = DBUtils.stream_query(params)

            counter = 0
            for pokemon in pokemon_list:
                if counter == stream_limit:
                    break

                data_id = pokemon["id"]
                skip = False
                if params["type"] == "weather":
                    for id_ in self.weather_cache[channel_id]:
                        skip = True
                        break
                else:
                    for id_ in self.cache[channel_id]:
                        if data_id == id_:
                            skip = True
                            break
                if skip:
                    continue

                user_obj = None
                if ("username" in pokemon.keys() and
                        pokemon["username"] in pogo_users.keys()):
                    user_id = pogo_users[pokemon["username"]]
                    user_obj = await self.bot.fetch_user(user_id)

                if params["type"] == "pokemon":
                    response = MsgUtils.msg_builder_pokemon(pokemon, params["embed"], user_obj)
                elif params["type"] == "gym":
                    response = MsgUtils.msg_builder_raid(pokemon, params["embed"])
                elif params["type"] == "weather":
                    response = MsgUtils.msg_builder_weather(pokemon, params["embed"])
                try:
                    channel = await self.bot.fetch_channel(channel_id)
                    await channel.send(content=response[0], embed=response[1])
                except:
                    continue

                self.cache[channel_id].append(data_id)
                self.weather_cache[channel_id].append(data_id)
                counter += 1
    
    @streamer.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

    @streamer.error
    async def streamer_error(self, error):
        logging.warning(error)

        self.streamer.restart()
        #logging.warning("STREAM RESTARTED")

async def setup(bot):
    await bot.add_cog(Streams(bot))

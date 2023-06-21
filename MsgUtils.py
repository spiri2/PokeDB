import discord
import re
import datetime
import time
import json
import requests
import logging
logging.basicConfig(level="warning")


from utils.ParseJson import ParseJson
from utils.DBUtils import DBUtils
ParseJson = ParseJson()
DBUtils = DBUtils()

from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="geoapiExercises")

from utils.PogoUtils import PogoUtils
PogoUtils = PogoUtils()

pokemon_list = ParseJson.read_file("pokemon_list.json")
move_list = ParseJson.read_file("moves.json")
weather_boost_info = ParseJson.read_file("poke_weather.json")
item_list = ParseJson.read_file("item_list.json")
translation = ParseJson.read_file("en.json")

class MsgUtils:
    def __init__(self):
        self.weather_emojis = {
                "1":"<a:sunny_boosted:1086001133681643611>",
                "2":"<a:rainy_boosted:1086017199405281411>",
                "3":"<a:partly_cloudy_boosted:1086001128761725068>",
                "4":"<a:cloudy_boosted:1086017193348694068>",
                "5":"<a:Windy_boosted:1086001138261840003>",
                "6":"<a:snowy_boosted:1086017487197446256>",
                "7":"<a:foggy_boosted:1086017195269697628>"
                }
    def get_gif(self, poke_id, shiny=False, item=False, leader=False):
        #name = name.lower()
        #name = re.sub(r"\((.*)\)","",name)
        #name = re.sub(r" ","",name)
        #url = f"https://play.pokemonshowdown.com/sprites/xyani/{name}.gif"
        url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/home/{poke_id}.png"
        if shiny:
            #url = f"https://play.pokemonshowdown.com/sprites/xyani-shiny/{name}.gif"
            url=f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/home/shiny/{poke_id}.png"
        if item:
            url=f"https://raw.githubusercontent.com/nileplumb/PkmnHomeIcons/master/UICONS/reward/item/{poke_id}.png"
        if leader:
            url=f"https://raw.githubusercontent.com/nileplumb/PkmnHomeIcons/master/UICONS/invasion/{poke_id}.png"
        response = requests.get(url, timeout=5, verify=True).status_code
        if response == 200:
            return url
        return

    def msg_builder_weather(self, data, embed=True):
        weather_names=["Sunny/Clear","Rainy","Partly Cloudy","Cloudy","Windy","Snow","Fog"]
        lat = str(data["latitude"])[0:9]
        lon = str(data["longitude"])[0:11]

        weather_id = data["gameplay_condition"]
        #weather_name = f"{self.weather_emojis[str(weather_id)]} {weather_names[weather_id-1]}"
        weather_name = f"{self.weather_emojis[str(weather_id)]} "

        try:
            location_dict = geolocator.reverse(str(data["latitude"])+","+str(data["longitude"])).raw["address"]
        except:
            location_dict = {}
            location_dict["country_code"] = ""

        country, city, state = "", "", ""
        if "country_code" in location_dict.keys():
            country = location_dict["country_code"].upper()
            country_emoji = ""
            if country:
                country_emoji = f":flag_{country.lower()}:"
        if "city" in location_dict.keys():
            city = location_dict["city"]+", "
        if "state" in location_dict.keys():
            state = location_dict["state"]+" "

        location = f"{country_emoji} {city}{state}{country}"

        msg = f"{lat}, {lon}"
        
        if not embed:
            msg += "\n"+weather_name
            msg += location

            return [msg,None]
        desc = location
        emb = discord.Embed(
                title=weather_name+desc,
                description="",
                color=discord.Color.blue())
        return [msg,emb]

    def msg_builder_quest(self, data, embed=True):
        lat = str(data["lat"])[0:9]
        lon = str(data["lon"])[0:11]
        google_maps = f"https://www.google.com/maps?q={lat},{lon}"
        apple_maps = f"https://www.apple.com/maps?daddr={lat},{lon}"
        poke_id = data["quest_pokemon_id"]
        if poke_id:
            pokemon_name = pokemon_list[poke_id-1]

        ar = ""
        if data["ar_scan_eligible"]:
            ar = "<:AR:1103208223495954442>"

        try:
            pokestop_emoji = "<:pokestop:1103208246132609025>"
            pokestop_name = ar+pokestop_emoji+data["name"]
        except:
            pokestop_name = ar+"Quest"

        expire_time = data["quest_timestamp"]
        expire_time = datetime.datetime.fromtimestamp(expire_time)
        expire_time = expire_time.strftime("%I:%M:%S %p")
        timeleft = datetime.timedelta(seconds=(data["quest_timestamp"] - time.time()))
        seconds = timeleft.total_seconds()
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        expire_time = f"(`{int(minutes)}m {int(seconds)}s`)"

        try:
            location_dict = geolocator.reverse(str(data["lat"])+","+str(data["lon"])).raw["address"]
        except:
            location_dict = {}
            location_dict["country_code"] = ""

        country, city, state = "", "", ""
        if "country_code" in location_dict.keys():
            country = location_dict["country_code"].upper()
            country_emoji = ""
            if country:
                country_emoji = f":flag_{country.lower()}:"
        if "city" in location_dict.keys():
            city = location_dict["city"]+", "
        if "state" in location_dict.keys():
            state = location_dict["state"]+" "

        location = f"\n{country_emoji} {city}{state}{country}"
        
        task = "**Task:** "
        task_info = data["quest_title"]
        target = data["quest_target"]
        task_info = translation["quest_title_"+task_info].replace("%{amount_0}",str(target))
        task += task_info
        task += "\n"

        rewards = "**Reward:** "
        reward_dict = json.loads(data["quest_rewards"])[0]["info"]
        image = None
        if "pokemon_id" in reward_dict.keys():
            pokemon_name = pokemon_list[reward_dict["pokemon_id"]-1]
            rewards += f"Pokemon: {pokemon_name}"
            image = self.get_gif(reward_dict["pokemon_id"])

        elif "item_id" in reward_dict.keys():
            item_name = ""
            for item in item_list:
                if item_list[item] == reward_dict["item_id"]:
                    item_name = item
                    item_name = item_name.replace("ITEM_","").replace("_"," ").lower().capitalize()

            rewards += f"Item: {item_name}"

        if "amount" in reward_dict.keys():
            rewards += f"(x{reward_dict['amount']})"
        rewards += "\n"

        if not embed:
            msg = pokestop_name
            msg += task
            msg += rewards
            msg += f"Ends: {expire_time}"
            msg += location
            msg += f"\n<{google_maps}> | <{apple_maps}>"

            return [msg,None]

        msg = f"{lat}, {lon}"
        desc = rewards
        desc += task
        desc += f"Ends: {expire_time}"
        desc += location
        desc += f"\n[Google]({google_maps}) | [Apple]({apple_maps})"

        emb = discord.Embed(
                title=pokestop_name,
                description=desc,
                color=discord.Color.blue())
        emb.set_thumbnail(url=image)
        return [msg,emb]

    def msg_builder_rocket(self, leader_data, pokestop_data, embed=True):
        lat = str(pokestop_data["lat"])[0:9]
        lon = str(pokestop_data["lon"])[0:11]
        google_maps = f"https://www.google.com/maps?q={lat},{lon}"
        apple_maps = f"https://www.apple.com/maps?daddr={lat},{lon}"

        pokestop_name = pokestop_data["name"]
        character_id = leader_data["`character`"]
        character_type = translation[f"grunt_{character_id}"]

        rewards = "**Reward:** "
        try:
            reward_dict = json.loads(pokestop_data["quest_rewards"])[0]["info"]
        except:
            return None
        image = None
        if "pokemon_id" in reward_dict.keys():
            pokemon_name = pokemon_list[reward_dict["pokemon_id"]-1]
            rewards += f"{pokemon_name}"
            image = self.get_gif(character_id, leader=True)

        elif "item_id" in reward_dict.keys():
            item_name = ""
            for item in item_list:
                if item_list[item] == reward_dict["item_id"]:
                    item_name = item
                    item_name = item_name.replace("ITEM_","").replace("_"," ").lower().capitalize()
                    image = self.get_gif(character_id, leader=True)

            rewards += f"{item_name}"

        else:
            return None

        expire_time = leader_data["expiration"]
        expire_time = datetime.datetime.fromtimestamp(expire_time)
        expire_time = expire_time.strftime("%I:%M:%S %p")
        timeleft = datetime.timedelta(seconds=(leader_data["expiration"] - time.time()))
        seconds = timeleft.total_seconds()
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        expire_time = f"(`{int(minutes)}m {int(seconds)}s`)"

        try:
            location_dict = geolocator.reverse(str(data["lat"])+","+str(data["lon"])).raw["address"]
        except:
            location_dict = {}
            location_dict["country_code"] = ""

        country, city, state = "", "", ""
        if "country_code" in location_dict.keys():
            country = location_dict["country_code"].upper()
            country_emoji = ""
            if country:
                country_emoji = f":flag_{country.lower()}:"
        if "city" in location_dict.keys():
            city = location_dict["city"]+", "
        if "state" in location_dict.keys():
            state = location_dict["state"]+" "

        location = f"\n{country_emoji} {city}{state}{country}"

        if not embed:
            msg = f"{lat},{lon}\n"
            msg += f"**Pokestop:** {pokestop_name}\n"
            msg += f"**Type:** {character_type}\n"
            #msg += f"{rewards}\n"
            msg += f"**Ends:** {expire_time}\n"
            msg += f"[Google](<{google_maps}>) | [Apple](<{apple_maps}>)"

            return [msg,None]

        msg = f"{lat},{lon}"
        desc = f"**Type:** {character_type}\n"
        #desc += f"{rewards}\n"
        desc += f"**Ends:** {expire_time}\n"
        desc += f"[Google](<{google_maps}>) | [Apple](<{apple_maps}>)"

        if not pokestop_name:
            pokestop_name = "Rocket Leader"

        emb = discord.Embed(
                title=pokestop_name,
                description=desc,
                color=discord.Color.blue())
        emb.set_thumbnail(url=image)

        return [msg,emb]

    def msg_builder_raid(self, data, embed=True):
        lat = str(data["lat"])[0:9]
        lon = str(data["lon"])[0:11]
        poke_id = data["raid_pokemon_id"]
        pokemon_name = pokemon_list[poke_id-1]
        ex = ""
        if data["ex_raid_eligible"]:
            ex = "<:EX:1103208230676606987>"
        cp = f"<:CP:1103208227358912512> {data['raid_pokemon_cp']}"
        if data["raid_pokemon_cp"] == 0:
            return None
        ms = "<:MS:1103208325069406228>"
        mystic = "<a:Mystic:1086001126891073617>"
        instinct = "<a:Instinct:1086001085317136526>"
        valor = "<a:Valor:1086001135493599442>"
        teams = [mystic,valor,instinct]
        team = teams[data["team_id"]-1]
        gender = "<:male2:1103208241204297748>" #male gender sign
        gender_num = data["raid_pokemon_gender"]
        if gender_num == 2:
            gender = "<:Female:1103209016001314854> "
        mega = ""
        if data["raid_level"] == 6:
            mega = "{Mega}"
        alignment = ""
        if data["raid_pokemon_alignment"]:
            alignment = "{Shadow}"

        expire_time = data["raid_end_timestamp"]
        expire_time = datetime.datetime.fromtimestamp(expire_time)
        expire_time = expire_time.strftime("%I:%M:%S %p")
        timeleft = datetime.timedelta(seconds=(data["raid_end_timestamp"] - time.time()))
        seconds = timeleft.total_seconds()
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        expire_time = f"(`{int(minutes)}m {int(seconds)}s`)"

        raid_battle = data["raid_spawn_timestamp"]
        raid_battle = datetime.datetime.fromtimestamp(raid_battle)
        raid_battle = raid_battle.strftime("%I:%M:%S %p")
        timeleft = datetime.timedelta(seconds=(data["raid_spawn_timestamp"] - time.time()))
        seconds = timeleft.total_seconds()
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        raid_battle = f"Starts: `{int(minutes)}m {int(seconds)}s`"

        move1 = move_list[data["raid_pokemon_move_1"]]["ename"]
        move2 = move_list[data["raid_pokemon_move_2"]]["ename"]

        try:
            location_dict = geolocator.reverse(str(data["lat"])+","+str(data["lon"])).raw["address"]
        except:
            location_dict = {}
            location_dict["country_code"] = ""

        country, city, state = "", "", ""
        if "country_code" in location_dict.keys():
            country = location_dict["country_code"].upper()
            country_emoji = ""
            if country:
                country_emoji = f":flag_{country.lower()}:"
        if "city" in location_dict.keys():
            city = location_dict["city"]+", "
        if "state" in location_dict.keys():
            state = location_dict["state"]+" "

        location = f"\n{country_emoji} {city}{state}{country}"

        if not embed:
            #msg = f"{team} {ex} {get_gif} **{data['name']}**\n"
            msg = f"{team} {ex} **{pokemon_name}** {mega} {alignment} {gender}\n"
            msg += f"{ms} {move1} / {move2}\n"
            #msg += f"{raid_battle}\n"
            msg += f"{cp} | {expire_time}\n"
            msg += f"{lat}, {lon}"
            msg += location

            return [msg,None]
        msg = f"{lat}, {lon}"
        desc = f"{cp} \n{ms} {move1}, {move2} \n"
        #desc += f"{raid_battle} \n"
        desc += f"Ends: {expire_time}"
        desc += location

        emb = discord.Embed(
                title=f"{team} {ex} {pokemon_name} {mega} {alignment} {gender}",
                description = desc,
                color=discord.Color.blue())
        gif_url = self.get_gif(poke_id)
        emb.set_thumbnail(url=gif_url)
        #emb.set_author(name=None, url=gif_url)

        return [msg,emb]

    def get_weather_boost(self, pokemon_id:str, weather_id:str):
        pokemon_id = str(pokemon_id)
        weather_id = str(weather_id)
        poke_type_info = weather_boost_info["pokemon"]
        boosted_types = weather_boost_info["weather"][weather_id]["types"]


        pokemon_types = poke_type_info[pokemon_id]["types"]

        for type_id in pokemon_types:
            if type_id in boosted_types:
                return f"{self.weather_emojis[weather_id]} (Boosted)\n"

        return ""

    def msg_builder_pokemon(self, data, embed=True, user_obj=None):
        user_list = ParseJson.read_file("pogo_users.json")

        poke_id = data["pokemon_id"]
        pokemon_name = pokemon_list[poke_id-1]
        form = data["form"]
        iv = "<:IV:1103208235558764544>"
        cp = "<:CP:1103208227358912512>"
        dsp = "<:DSP:1103208228793360394>"
        lvl = "<:LV:1103208238268293192>"
        ms = "<:MS:1103208325069406228>"
        shiny = "<a:Shiny:1086001130544320634>"
        gender = "<:male2:1103208241204297748>" #male gender sign
        gender_num = data["gender"]
        device_name = DBUtils.get_device_name(data["username"])[0]
        if gender_num == 2:
            gender = "<:Female:1103209016001314854> "
        star = "<:stardust:1120857081625456660>"
        rare_candy = "<:rarecandy:1120706487354916986>"
        xl_candy = "<:xlcandy:1120707243101388820>"

        boosted = self.get_weather_boost(poke_id, data["weather"])

        expire_time = data["expire_timestamp"]
        expire_time = datetime.datetime.fromtimestamp(expire_time)
        expire_time = expire_time.strftime("%I:%M:%S %p")
        timeleft = datetime.timedelta(seconds=(data["expire_timestamp"] - time.time()))
        seconds = timeleft.total_seconds()
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        expire_time = f"({dsp} `{int(minutes)}m {int(seconds)}s`)"

        move1 = move_list[data["move_1"]]["ename"]
        move2 = move_list[data["move_2"]]["ename"]

        cost_to_40 = PogoUtils.calculate_powerup_cost(data["level"], 40)
        cost_to_50 = PogoUtils.calculate_powerup_cost(data["level"], 50)

        try:
            location_dict = geolocator.reverse(str(data["lat"])+","+str(data["lon"])).raw["address"]
        except:
            location_dict = {}
            location_dict["country_code"] = ""

        country, city, state = "", "", ""
        if "country_code" in location_dict.keys():
            country = location_dict["country_code"].upper()
            country_emoji = ""
            if country:
                country_emoji = f":flag_{country.lower()}:"
        if "city" in location_dict.keys():
            city = location_dict["city"]+", "
        if "state" in location_dict.keys():
            state = location_dict["state"]+" "

        location = f"\n{country_emoji} {city}{state}{country}"

        pvp_sect = ""
        if data["pvp"]:
            data_pvp = json.loads(data["pvp"])

            great_rank, ultra_rank, lc_rank = ["","",""]
            if "great" in data_pvp.keys():
                great_rank = data_pvp["great"][0]["rank"]
            if "ultra" in data_pvp.keys():
                ultra_rank = data_pvp["ultra"][0]["rank"]
            '''
            if "little" in data_pvp.keys():
                lc_rank = data_pvp["little"][0]["rank"]
            pvp_sect = f" {great_rank} / {ultra_rank} / {lc_rank}\n"
            '''
            #To add little cup delete pvp_sect =  and uncomment lines above.
            gl_emoji = "<:Great_League:1070141365536706580>"
            ul_emoji = "<:Ultra_League:1070141368132960257>"

            if great_rank:
                pvp_sect += f"{gl_emoji} rank **{great_rank}** " 
            if ultra_rank:
                pvp_sect += f"{ul_emoji} rank **{ultra_rank}**"

        if not embed:
            if data["is_ditto"]:
                pokemon_name = f"Ditto [{pokemon_list[data['display_pokemon_id']-1]}]"
            msg = f"**{pokemon_name}** {gender} {expire_time}\n"
            msg += boosted
            msg += f"**{iv} {data['iv']}** ({data['atk_iv']}/{data['def_iv']}/{data['sta_iv']}) "
            msg += f"**{cp} {data['cp']} {lvl} {data['level']}**\n"
            msg += f"{ms} {move1} / {move2}"
            msg += f"**__Power Up Cost__**:\n{lvl}**40** ={star}{cost_to_40['stardust']}{rare_candy}{cost_to_40['candy']}\n"
            msg += f"{lvl}**50** ={star}{cost_to_50['stardust']}{rare_candy}{cost_to_50['candy']}{xl_candy}{cost_to_50['xl_candy']}"
            #msg += pvp_sect
            msg += f"{location}\n"
            msg +=  f"{str(data['lat'])[0:9]}, {str(data['lon'])[0:11]}"
            if data["shiny"]:
                #msg += f"{shiny} **{data['username']}** found a shiny {shiny}"
                msg += f"Device: {device_name}\n"
                msg += f"{shiny} **Shiny {pokemon_name} found! {shiny}"
                if user_obj:
                    msg += f"\n{user_obj.mention}"
            msg += "\n---"
            return [msg,None]

        msg = f"{str(data['lat'])[0:9]}, {str(data['lon'])[0:11]}"
        desc = ""
        desc += boosted
        desc += f"{iv}**{data['iv']}** ({data['atk_iv']}/{data['def_iv']}/{data['sta_iv']}) " 
        desc += f"{cp}**{data['cp']}** {lvl}**{data['level']}**\n"
        desc += f"{ms} {move1} / {move2}\n"
        #desc += pvp_sect
        desc += f"**__Power Up Cost__**:\n{lvl}**40**:{star}{cost_to_40['stardust']} {rare_candy}{cost_to_40['candy']}\n"
        desc += f"{lvl}**50**:{star}{cost_to_50['stardust']} {rare_candy}{cost_to_50['candy']} {xl_candy}{cost_to_50['xl_candy']}"
        desc += f"{location}\n"

        if data["shiny"]:
            if user_obj:
                msg += f"\n{user_obj.mention}"
            desc+=f"{shiny} {device_name} ({data['username']})"
       
        emb = discord.Embed(
                title=f"{pokemon_name} {gender} {expire_time}",
                description = desc,
                color=discord.Color.blue())
        if data["is_ditto"]:
            emb = discord.Embed(
                    title=f"Ditto [{pokemon_list[data['display_pokemon_id']-1]}] {gender} {expire_time}",
                    description = desc,
                    color=discord.Color.blue())
        gif_url = self.get_gif(poke_id)
        if data["shiny"]:
            gif_url = self.get_gif(poke_id, True)
        emb.set_thumbnail(url=gif_url)
        #emb.set_footer(text=f"{location}", icon=country_emoji)

        return [msg,emb]

    def msg_builder_stats(self, pokemon_stats, account_stats, stats_time, 
            device_stats):
        pokemon_labels = [
                "<:pokeball:1103208408712216607> Pokemon: ",
                ":100:IV: ",
                "<a:Shiny:1086001130544320634> Shiny: ",
                "<:raid:1107859808926826536> Raids: ",
                "<:pokestop:1103208246132609025> Quests: ",
                "<:rocketteam:1107860171885117460> Invasions: "
                ]
        account_labels = [
                "<:check:1103208226155143209> Accounts Created: ",
                "<:check:1103208226155143209> Accounts Level 30+: ",
                "<:check:1103208226155143209> Accounts Level 0: ",
                "<:check:1103208226155143209> Accounts Available: ",
                "<:check:1103208226155143209> Accounts In Use: ",
                "<:warned:1107863956023951381> Accounts Disabled: ",
                "<:warned:1107863956023951381> Accounts w/ Warning: ",
                ":exclamation: Accounts Failed: "
                ]


        daily_desc = ""
        multiday_desc = ""

        count = 0
        for key in pokemon_stats:
            daily_desc += f"{pokemon_labels[count]}"
            daily_desc += f"{format(pokemon_stats[key][0],',d')}\n"
            multiday_desc += f"{pokemon_labels[count]}"
            multiday_desc += f"{format(pokemon_stats[key][1],',d')}\n"

            count+=1

        stats_time = stats_time[0].strftime("%m/%d/%Y")
        daily_emb = discord.Embed(
                title=f"Daily Stats - {stats_time}",
                description=daily_desc,
                color=discord.Color.blue())
        multiday_emb = discord.Embed(
                title="Weekly Avg Stats",
                description=multiday_desc,
                color=discord.Color.blue())

        account_desc = ""

        count = 0
        for key in account_stats:
            account_desc += account_labels[count]
            account_desc += f"{format(account_stats[key],',d')}\n"

            count +=1

        account_emb = discord.Embed(
                title="Account Stats",
                description=account_desc,
                color=discord.Color.blue())

        device_desc = "__UUID **|** Instance **|** Account Name__\n"
        for device in device_stats:
            online = "<a:alert:1109202762987737179>"
            timestamp = time.time()-60
            if device["last_seen"] > timestamp:
                online = "<:online:1109204848156627074>"
            device_desc += f"{online}{device['uuid']}**/**"
            device_desc += f"{device['instance_name']}**/**"
            #device_desc += f"<:character:1108447423065501757> {device['account_username']}\n"
            device_desc += f"{device['account_username']}\n"

        device_emb = discord.Embed(
                title="Device Stats",
                description=device_desc,
                color=discord.Color.blue())

        return [daily_emb, multiday_emb, account_emb, device_emb]



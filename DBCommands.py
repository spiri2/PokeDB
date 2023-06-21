import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.app_commands import Group
from discord.ext.commands import GroupCog
import asyncio
import logging

from utils.ParseJson import ParseJson
from utils.DBUtils import DBUtils
from utils.MsgUtils import MsgUtils
from utils.Verification import Verification
ParseJson = ParseJson()
DBUtils = DBUtils()
MsgUtils = MsgUtils()
Verification = Verification()

config = ParseJson.read_file("config.json")
pokemon_list = ParseJson.read_file("pokemon_list.json")
move_list = ParseJson.read_file("moves.json")
item_list = ParseJson.read_file("item_list.json")

logging.basicConfig(level="WARNING")

class MenuSelect(discord.ui.Select):
    def __init__(self, command_name):
        self.command_name = command_name
        self.weather_options = [
                discord.SelectOption(label="Sunny"),
                discord.SelectOption(label="Rainy"),
                discord.SelectOption(label="Partly Cloudy"),
                discord.SelectOption(label="Cloudy"),
                discord.SelectOption(label="Windy"),
                discord.SelectOption(label="Snow"),
                discord.SelectOption(label="Fog")
                ]
        self.leader_options = [
                discord.SelectOption(label="Grunt"),
                discord.SelectOption(label="Arlo"),
                discord.SelectOption(label="Cliff"),
                discord.SelectOption(label="Sierra"),
                discord.SelectOption(label="Giovanni"),
                discord.SelectOption(label="Jessie"),
                discord.SelectOption(label="James")
                ]
        self.table_options = [
                discord.SelectOption(label="Account"),
                discord.SelectOption(label="Device"),
                discord.SelectOption(label="Pokemon"),
                discord.SelectOption(label="Quest"),
                discord.SelectOption(label="Weather")
                ]
        command_info = {"wsearch":["Select weather option.",self.weather_options],
                "weather_track":["Select weather option.",self.weather_options],
                "rocketsearch":["Select leader.",self.leader_options],
                "truncate":["Select table.",self.table_options]}

        super().__init__(placeholder=command_info[self.command_name][0], 
                min_values=1,
                max_values=1,
                options=command_info[self.command_name][1])

    async def callback(self, interaction: discord.Interaction):
        streams = ParseJson.read_file("streams.json")
        config = ParseJson.read_file("config.json")
        if self.command_name == "wsearch" or self.command_name == "weather_track":
            for index, item in enumerate(self.weather_options):
                if item.value == self.values[0]:
                    weather_id = index+1

        await interaction.response.defer(ephemeral=True)

        if self.command_name == "wsearch":
            weather_locations = DBUtils.query_weather_id(weather_id)
            ctr = 0
            for location in weather_locations:
                if ctr == 20:
                    break

                msg = MsgUtils.msg_builder_weather(location, (interaction.channel.id in config["psearch_embeds"]))
                await interaction.followup.send(msg[0], ephemeral=True, embed=msg[1])
                ctr += 1

            if not weather_locations:
                await interaction.followup.send("No weather locations found with requested parameters.",ephemeral=True)

        if self.command_name == "weather_track":
            args = {"gameplay_condition":weather_id,"embed":True,"type":"weather",}
            channel_id = interaction.channel.id
            streams[channel_id] = args
            ParseJson.save_file("streams.json", streams)

            msg = f"Data Stream Created in {interaction.channel.mention}.\n```"
            for argument in args:
                msg += f"{argument.capitalize()}: "
                if isinstance(args[argument], list):
                    msg += f"Min: {args[argument][0]}, Max: {args[argument][1]}\n"
                    continue
                msg += f"{args[argument]}\n"
            msg += "```"
            await interaction.followup.send(msg, ephemeral=True)

        if self.command_name == "truncate":
            table_name = self.values[0].lower()
            if table_name == "quest":
                table_name = "pokestop"
            '''
            status = DBUtils.truncate(table_name)

            if status == 1:
                await interaction.followup.send("Truncate success.", ephemeral=True)
            else:
                await interaction.followup.send(f"Truncate failed.\n```{status}```", ephemeral=True)
            '''
            view = ButtonView(table_name)
            await interaction.followup.send(f"Truncate `{table_name}`?",view=view, ephemeral=True)

        if self.command_name == "rocketsearch":
            translation = ParseJson.read_file("en.json")

            grunt_id_list = list(range(4,40))
            grunt_id_list.extend(list(range(45,53)))
            grunt_id_list.extend(list(range(55,91)))
            leader_ids = {
                    "grunt":grunt_id_list,
                    "cliff":41,
                    "arlo":42,
                    "sierra":43,
                    "giovanni":44,
                    "jessie":53,
                    "james":54}
            selected_leader = self.values[0].lower()
            selected_leader_id = leader_ids[selected_leader]

            pokestop_id_list = []
            leader_pokestops = DBUtils.query_leaders(selected_leader_id)
            for leader in leader_pokestops:
                pokestop_id_list.append(leader["pokestop_id"])

            actual_pokestops = DBUtils.query_pokestops(pokestop_id_list)

            ctr = 0 
            for leader in leader_pokestops:
                if ctr == 20:
                    break
                pokestop = None
                for poke in actual_pokestops:
                    if poke["id"] == leader["pokestop_id"]:
                        pokestop = poke
                        break
                if not pokestop:
                    continue

                msg = MsgUtils.msg_builder_rocket(leader, pokestop, 
                        (interaction.channel.id in config["psearch_embeds"]))
                if not msg:
                    continue

                await interaction.followup.send(msg[0], embed=msg[1], ephemeral=True)
                ctr += 1
            if not leader_pokestops:
                await interaction.followup.send("No rocket leaders found.", ephemeral=True)

class MenuView(discord.ui.View):
    def __init__(self, command):
        super().__init__()
        self.add_item(MenuSelect(command))

class ConfirmButton(discord.ui.Button):
    def __init__(self, table_name):
        super().__init__(label="Confirm",style=discord.ButtonStyle.green)
        self.table_name = table_name

    async def callback(self, interaction):
        status = DBUtils.truncate(self.table_name)

        if status == 1:
            await interaction.response.edit_message(content="Truncate success.", view=None)
        else:
            await interaction.response.edit_message(content=f"Truncate failed.\n```{status}```", view=None)

class CancelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Cancel",style=discord.ButtonStyle.red)

    async def callback(self, interaction):
        await interaction.response.edit_message(content="Truncate canceled.", view=None)

class ButtonView(discord.ui.View):
    def __init__(self, table_name):
        super().__init__()

        self.add_item(ConfirmButton(table_name))
        self.add_item(CancelButton())

class DBCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    truncate_group = Group(name="truncate", description="Owner only truncate commands.")

    @truncate_group.command(name="table", description="Clear RDM tables.")
    async def truncate_table(self, interaction:discord.Interaction):
        if not Verification.verify_owner(interaction.user.id):
            await interaction.response.send_message("You are not authorized to use this command.",
                    ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        view = MenuView("truncate")
        await interaction.followup.send(view=view, ephemeral=True)

    @truncate_group.command(name="account", description="Remove account from RDM.")
    async def truncate_account(self, interaction:discord.Interaction, account_username:str):
        if not Verification.verify_owner(interaction.user.id):
            await interaction.response.send_message("You are not authorized to use this command.", 
                    ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        status = DBUtils.truncate_account(account_username)

        await interaction.followup.send(f"{status}", ephemeral=True)

            

    @app_commands.command(name="psearch", description="Search by Pokemon name or min. IV")
    async def psearch(self, interaction:discord.Interaction, name:str, min_iv:int=0,
            min_cp:int=0, min_lvl:int=0):
        streams = ParseJson.read_file("streams.json")
        config = ParseJson.read_file("config.json")
        channel_list = config["channel_whitelist"]
        if interaction.channel.id not in channel_list:
            await interaction.response.send_message(
                    f"{interaction.channel.mention} is not whitelisted for this command.", ephemeral=True)
            return
        user_roles = interaction.user.roles
        role_list = config["role_whitelist"]
        auth = False
        for role in user_roles:
            if role.id in role_list:
                auth = True
                break
        if not auth:
            await interaction.response.send_message("None of your roles are whitelisted for this command.",
                    ephemeral=True)
            return
        if not name and not min_iv:
            await interaction.response.send_message("Please input at least one parameter.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        pokemon_id = name
        if name:
            name = name.lower().capitalize()
            try:
                pokemon_id = pokemon_list.index(name)+1
            except ValueError:
                await interaction.followup.send(f"Pokemon `{name}` doesn't exist.")
                return

        pokemon = DBUtils.query_id(pokemon_id, min_iv, min_cp, min_lvl)

        ctr = 0
        for poke in pokemon:
            if ctr == 20:
                break

            msg = MsgUtils.msg_builder_pokemon(poke, (interaction.channel.id in config["psearch_embeds"]))
            await interaction.followup.send(msg[0], ephemeral=True, embed=msg[1])
            ctr += 1

        if not pokemon:
            await interaction.followup.send("No pokemon found with requested parameters.")

    @psearch.error
    async def psearch_error(self, interaction, error):
        logging.warning(error)
        await interaction.channel.send("There was an error. Please try again or contact an admin.")

    @app_commands.command(name="rsearch", description="Search raids by Pokemon name or tier.")
    async def rsearch(self, interaction:discord.Interaction, name:str="", tier:int=0):
        config = ParseJson.read_file("config.json")
        channel_list = config["channel_whitelist"]
        if interaction.channel.id not in channel_list:
            await interaction.response.send_message(
                    f"{interaction.channel.mention} is not whitelisted for this command.", ephemeral=True)
            return
        user_roles = interaction.user.roles
        role_list = config["role_whitelist"]
        auth = False
        for role in user_roles:
            if role.id in role_list:
                auth = True
                break
        if not auth:
            await interaction.response.send_message("None of your roles are whitelisted for this command.",
                    ephemeral=True)
            return
        if not name and not tier:
            await interaction.response.send_message("Please input at least one parameter.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        pokemon_id = name
        if name:
            name = name.lower().capitalize()
            try:
                pokemon_id = pokemon_list.index(name)+1
            except ValueError:
                await interaction.followup.send(f"Pokemon `{name}` doesn't exist.")
                return

        raid_list = DBUtils.query_raid_id(pokemon_id, tier)

        ctr = 0
        for raid in raid_list:
            if ctr == 20:
                break

            msg = MsgUtils.msg_builder_raid(raid, (interaction.channel.id in config["psearch_embeds"]))
            if not msg:
                continue
            await interaction.followup.send(msg[0], ephemeral=True, embed=msg[1])
            ctr += 1

        if not raid_list:
            await interaction.followup.send("No raids found with requested parameters.")

    @rsearch.error
    async def rsearch_error(self, interaction, error):
        logging.warning(error)
        await interaction.channel.send("There was an error. Please try again or contact an admin.")
    
    @app_commands.command(name="wsearch", description="Search for weather conditions.")
    async def wsearch(self, interaction:discord.Interaction):
        config = ParseJson.read_file("config.json")
        channel_list = config["channel_whitelist"]
        if interaction.channel.id not in channel_list:
            await interaction.response.send_message(
                    f"{interaction.channel.mention} is not whitelisted for this command.", ephemeral=True)
            return
        user_roles = interaction.user.roles
        role_list = config["role_whitelist"]
        auth = False
        for role in user_roles:
            if role.id in role_list:
                auth = True
                break
        if not auth:
            await interaction.response.send_message("None of your roles are whitelisted for this command.",
                    ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        view = MenuView("wsearch")
        await interaction.followup.send(view=view, ephemeral=True)

    @wsearch.error
    async def wsearch_error(self, interaction, error):
        logging.warning(error)
        await interaction.channel.send("There was an error. Please try again or contact an admin.")

    @app_commands.command(name="rocketsearch", description="Search for team leaders.")
    async def rocketsearch(self, interaction:discord.Interaction):
        config = ParseJson.read_file("config.json")
        channel_list = config["channel_whitelist"]
        if interaction.channel.id not in channel_list:
            await interaction.response.send_message(
                    f"{interaction.channel.mention} is not whitelisted for this command.", ephemeral=True)
            return
        user_roles = interaction.user.roles
        role_list = config["role_whitelist"]
        auth = False
        for role in user_roles:
            if role.id in role_list:
                auth = True
                break
        if not auth:
            await interaction.response.send_message("None of your roles are whitelisted for this command.",
                    ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        view = MenuView("rocketsearch")
        await interaction.followup.send(view=view, ephemeral=True)

    @app_commands.command(name="qsearch", description="Search for quests.")
    async def qsearch(self, interaction: discord.Interaction, query:str):
        config = ParseJson.read_file("config.json")
        channel_list = config["channel_whitelist"]
        if interaction.channel.id not in channel_list:
            await interaction.response.send_message(
                    f"{interaction.channel.mention} is not whitelisted for this command.", ephemeral=True)
            return
        user_roles = interaction.user.roles
        role_list = config["role_whitelist"]
        auth = False
        for role in user_roles:
            if role.id in role_list:
                auth = True
                break
        if not auth:
            await interaction.response.send_message("None of your roles are whitelisted for this command.",
                    ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        field = None
        try:
            poke_id = pokemon_list.index(query.lower().capitalize())+1
            query = f'%"pokemon_id":{poke_id},%'
            field = "quest_rewards"
        except ValueError:
            pass

        for item in item_list:
            check_item = item.replace("ITEM_","").replace("_"," ").lower()
            if query == check_item:
                query = item_list[item]
                field = "quest_item_id"

        if not field:
            await interaction.followup.send(f"`{query}` not identified as pokemon or item.", 
                    ephemeral=True)
            return

        quest_list = DBUtils.query_quest(query, field)

        ctr = 0
        for quest in quest_list:
            if ctr == 20:
                break

            msg = MsgUtils.msg_builder_quest(quest, (interaction.channel.id in config["psearch_embeds"]))
            if not msg:
                continue
            await interaction.followup.send(msg[0], ephemeral=True, embed=msg[1])
            ctr += 1

        if not quest_list:
            await interaction.followup.send("No quests found with requested parameters.")

    @app_commands.command(name="pset", description="Set params for /psearch (Admin-Only)")
    async def pset(self, interaction:discord.Interaction, role:discord.Role=None,
            channel:discord.abc.GuildChannel=None):
        if not Verification.verify_on_whitelist(interaction.user.id,
                interaction.user.roles):
            await interaction.response.send_message("You aren't authorized to use this command.", ephemeral=True)
            return
        if not role and not channel:
            await interaction.response.send_message("Please input at least one parameter.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        role_list = config["role_whitelist"]
        channel_list = config["channel_whitelist"]

        msg = ""
        if role:
            if role.id in role_list:
                config["role_whitelist"].remove(role.id)
                msg += f"{role.mention} Removed from whitelist.\n"
            else:
                config["role_whitelist"].append(role.id)
                msg += f"{role.mention} Added to whitelist.\n"

        if channel:
            if channel.id in channel_list:
                config["channel_whitelist"].remove(channel.id)
                msg+= f"{channel.mention} Removed from whitelist.\n"
            else:
                config["channel_whitelist"].append(channel.id)
                msg+= f"{channel.mention} Added to whitelist.\n"

        ParseJson.save_file("config.json", config)
        msg += "Config file updated."
        await interaction.followup.send(msg, ephemeral=True)
    
    @pset.error
    async def pset_error(self, interaction, error):
        await interaction.channel.send("There was an error. Please try again or notify an admin.")

    track_group = Group(name="track", description="Set up data streams. (Admin-Only)")
    
    @track_group.command(name="pokemon", description="Set up a continuous pokemon stream. (Admin-Only)")
    async def track_pokemon(self, interaction:discord.Interaction, pokemon_name:str=None, min_cp:int=0,
            max_cp:int=5000, min_lvl:int=0, max_lvl:int=100, min_iv:int=0, max_iv:int=100, 
            shiny_only:bool=False):

        streams = ParseJson.read_file("streams.json")
        if not Verification.verify_on_whitelist(interaction.user.id,
                interaction.user.roles):
            await interaction.response.send_message("You aren't authorized to use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        pokemon_id = None 
        if pokemon_name:
            pokemon_name = pokemon_name.lower().capitalize()
            try:
                pokemon_id = pokemon_list.index(pokemon_name)+1
            except ValueError:
                await interaction.followup.send(f"Pokemon `{pokemon_name}` doesn't exist.")
                return

        args = {"pokemon_id":pokemon_id,"cp":[min_cp,max_cp],"level":[min_lvl,max_lvl],"iv":[min_iv,max_iv],
                "shiny":shiny_only,"embed":True,"type":"pokemon"}

        channel_id = interaction.channel.id
        streams[channel_id] = args
        ParseJson.save_file("streams.json", streams)

        msg = f"Data Stream Created in {interaction.channel.mention}.\n```"
        for argument in args:
            msg += f"{argument.capitalize()}: "
            if isinstance(args[argument], list):
                msg += f"Min: {args[argument][0]}, Max: {args[argument][1]}\n"
                continue
            msg += f"{args[argument]}\n"
        msg += "```"
        await interaction.followup.send(msg, ephemeral=True)

    @track_group.command(name="raid", description="Set up a continuous raid stream. (Admin-Only)")
    async def track_raid(self, interaction:discord.Interaction, pokemon_name:str=None,tier:int=0,
            min_tier:int=0,max_tier:int=10):
        streams = ParseJson.read_file("streams.json")
        if not Verification.verify_on_whitelist(interaction.user.id,
                interaction.user.roles):
            await interaction.response.send_message("You aren't authorized to use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        pokemon_id = None 
        if pokemon_name:
            pokemon_name = pokemon_name.lower().capitalize()
            try:
                pokemon_id = pokemon_list.index(pokemon_name)+1
            except ValueError:
                await interaction.followup.send(f"Pokemon `{pokemon_name}` doesn't exist.")
                return

        args = {"pokemon_id":pokemon_id,"raid_level":[min_tier,max_tier],"embed":True,"type":"gym"}
        if tier > 0:
            args = {"pokemon_id":pokemon_id,"raid_level":tier,"embed":True,"type":"gym"}

        channel_id = interaction.channel.id
        streams[channel_id] = args
        ParseJson.save_file("streams.json", streams)

        msg = f"Data Stream Created in {interaction.channel.mention}.\n```"
        for argument in args:
            msg += f"{argument.capitalize()}: "
            if isinstance(args[argument], list):
                msg += f"Min: {args[argument][0]}, Max: {args[argument][1]}\n"
                continue
            msg += f"{args[argument]}\n"
        msg += "```"
        await interaction.followup.send(msg, ephemeral=True)

    @track_group.command(name="weather", description="Set up a continuous weather stream. (Admin-Only)")
    async def track_weather(self, interaction:discord.Interaction):
        if not Verification.verify_on_whitelist(interaction.user.id,
                interaction.user.roles):
            await interaction.response.send_message("You aren't authorized to use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        view = MenuView("weather_track")
        await interaction.followup.send(view=view, ephemeral=True)


    @app_commands.command(name="untrack", 
    description="Remove a data stream from the current channel. (Admin-Only)")
    async def untrack(self, interaction: discord.Interaction):
        streams = ParseJson.read_file("streams.json")
        if not Verification.verify_on_whitelist(interaction.user.id,
                interaction.user.roles):
            await interaction.response.send_message("You aren't authorized to use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            del streams[str(interaction.channel.id)]
            ParseJson.save_file("streams.json", streams)
        except Exception as e:
            await interaction.followup.send(f"{interaction.channel.mention} has no data stream.", ephemeral=True)
            return
        await interaction.followup.send(f"Data stream removed from {interaction.channel.mention}", 
                ephemeral=True)

    @app_commands.command(name="stats",
            description="Show pokemon and account stats. (Admin-Only)")
    async def stats(self, interaction: discord.Interaction):
        if not Verification.verify_on_whitelist(interaction.user.id, 
                interaction.user.roles):
            await interaction.response.send_message("You aren't authorized to use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        stats_info = DBUtils.get_stats()
        embed_list = MsgUtils.msg_builder_stats(stats_info[0], stats_info[1],
                stats_info[2], stats_info[3])

        await interaction.followup.send(embeds=embed_list, ephemeral=True)
    
async def setup(bot):
    await bot.add_cog(DBCommands(bot))

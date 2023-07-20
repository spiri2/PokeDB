import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.app_commands import Group
from discord.ext.commands import GroupCog
import asyncio
import logging

from utils.ParseJson import ParseJson
from utils.Verification import Verification
from utils.SSHUtils import SSHUtils
from utils.DBUtils import DBUtils
ParseJson = ParseJson()
Verification = Verification()
SSHUtils = SSHUtils()
DBUtils = DBUtils()

logging.basicConfig(level="WARNING")

class GeneralCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def sync(self, ctx):
        if not Verification.verify_on_whitelist(ctx.message.author.id,
                ctx.message.author.roles):
            await ctx.send("You don't have permissions for this command.", ephemeral=True)
            return

        fmt = await ctx.bot.tree.sync()
        await ctx.send(f"Synced {len(fmt)} cmds.")

    toggle = Group(name="toggle", description="Admin Only Config Commands.")
    admin_group = Group(parent=toggle, name="admin", description="Admin Only Config Commands.")



    @toggle.command(name="embed", description="Toggle embedded posts for a channel's stream.")
    async def embed(self, interaction: discord.Interaction):
        streams = ParseJson.read_file("streams.json")
        config = ParseJson.read_file("config.json")

        psearch_embeds = config["psearch_embeds"]
        psearch_whitelist = config["channel_whitelist"]

        await interaction.response.defer(ephemeral=True)

        if not Verification.verify_on_whitelist(interaction.user.id,
                interaction.user.roles):
            await interaction.followup.send("You don't have permissions for this command.", ephemeral=True)
            return

        channel = interaction.channel

        for channel_id in streams:
            if int(channel_id) != channel.id:
                continue
            streams[channel_id]["embed"] = not streams[channel_id]["embed"]
            ParseJson.save_file("streams.json", streams)

            msg = f"{channel.mention}'s stream embed status updated:\n{not streams[channel_id]['embed']} --> "
            msg += f"{streams[channel_id]['embed']}"
            await interaction.followup.send(msg, ephemeral=True)
            break

        if channel.id in psearch_whitelist:
            if channel.id in psearch_embeds:
                config["psearch_embeds"].remove(channel.id)
            else:
                config["psearch_embeds"].append(channel.id)
            ParseJson.save_file("config.json", config)

            embedded_posts = (channel.id in config["psearch_embeds"])
            msg = f"{channel.mention}'s search embed status updated:\n{not embedded_posts} --> "
            msg += f"{embedded_posts}"
            await interaction.followup.send(msg, ephemeral=True)


        '''
        await interaction.followup.send(
                f"{channel.mention} not valid. Not whitelisted or contains no stream.",
                ephemeral=True)
        '''
        
    @toggle.command(name="ping", description="Connect PoGo usernames to discord users.")
    async def ping(self, interaction:discord.Interaction, pogo_name:str, discord_name:discord.User):
        await interaction.response.defer(ephemeral=True)

        if not Verification.verify_on_whitelist(interaction.user.id,
                interaction.user.roles):
            await interaction.followup.send("You don't have permissions for this command.", ephemeral=True)
            return

        user_list = ParseJson.read_file("pogo_users.json")
        if pogo_name in user_list:
            if user_list[pogo_name] != discord_name.id:
                user_list[pogo_name] = discord_name.id
                msg = "Link Updated:\n"
            else:
                del user_list[pogo_name]
                msg = "Link Removed:\n"
        else:
            user_list[pogo_name] = discord_name.id
            msg = "Link Added:\n"

        ParseJson.save_file("pogo_users.json", user_list)

        msg += f"{pogo_name} --> {discord_name.mention}"
        await interaction.followup.send(msg, ephemeral=True)

    @admin_group.command(name="add", description="Add users/roles to admin whitelist.")
    async def admin_add(self, interaction:discord.Interaction, item_id:str):
        if not Verification.verify_owner(interaction.user.id):
            await interaction.response.send_message("You're not authorized to use this command.",
                    ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)

        try:
            item_id = int(item_id)
        except:
            raise Exception
        
        id_added = Verification.modify_whitelist(item_id)
        if not id_added:
            await interaction.followup.send("Failure adding id.", ephemeral=True)
        await interaction.followup.send("ID added successfully.", ephemeral=True)

    @admin_add.error
    async def admin_add_error(self, interaction, error):
        await interaction.channel.send("There was an error.")

    @admin_group.command(name="remove", description="Remove users/roles from admin whitelist.")
    async def admin_remove(self, interaction:discord.Interaction, item_id:str):
        if not Verification.verify_owner(interaction.user.id):
            await interaction.response.send_message("You're not authorized to use this command.",
                    ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            item_id = int(item_id)
        except:
            raise Exception
        
        id_added = Verification.modify_whitelist(item_id, False)
        if not id_added:
            await interaction.followup.send("Failure removing id.", ephemeral=True)
        await interaction.followup.send("ID removed successfully.", ephemeral=True)

    @admin_add.error
    async def admin_add_error(self, interaction, error):
        await interaction.channel.send("There was an error.")


    rdm = Group(name="rdm", description="Owner Only RDM commands.")

    @rdm.command(name="update", description="Update RDM. (Owner-Only)")
    async def rdm_update(self, interaction:discord.Interaction):
        if not Verification.verify_owner(interaction.user.id):
            await interaction.response.send_message("You're not authorized to use this command.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        await interaction.followup.send("Beginning update. Please wait.", ephemeral=True)

        success = SSHUtils.rdm_update()

        if success[0]:
            output = success[1]
            print(output)
            if len(output) > 500:
                output = output[:500]
            for item in output:
                if "VersionManager" in output:
                    output = item
            #await interaction.followup.send("RDM Updated.\n`{output}`", ephemeral=True)
            await interaction.followup.send("RDM Updated.", ephemeral=True)
        else:
            error = success[1]
            for item in error:
                if "up-to-date" in item:
                    error = "Already updated."
                else:
                    error = "See console."
            print(error)

            await interaction.followup.send(f"Failed.\n`{error}`", ephemeral=True)

    @rdm.command(name="bsod", description="Reset Disabled Accounts (Owner-Only)")
    async def reset_accounts(self, interaction:discord.Interaction):
        if not Verification.verify_owner(interaction.user.id):
            await interaction.response.send_message("You're not authorized to use this command.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        msg = DBUtils.reset_accounts()
        await interaction.followup.send(msg, ephemeral=True)

    @rdm.command(name="restart", description="Restart RDM. (Owner-Only)")
    async def rdm_restart(self, interaction:discord.Interaction):
        if not Verification.verify_owner(interaction.user.id):
            await interaction.response.send_message("You're not authorized to use this command.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        await interaction.followup.send("Restarting... please wait.", ephemeral=True)

        msg = SSHUtils.rdm_restart()

        if msg[0]:
            output = msg[1]
            await interaction.followup.send("Restarted successfully.", ephemeral=True)
        else:
            error = msg[1]
            try:
                await interaction.followup.send(f"Failed.\n`{error}`", ephemeral=True)
            except:
                await interaction.follow.send("Failed. See console.", ephemeral=True)

    format_cmd = Group(name="format", description="Admin Only Formatting Commands.")

    @format_cmd.command(name="view", description="See current formats. (Admin-Only)")
    async def format_view(self, interaction=discord.Interaction):
        if not Verification.verify_on_whitelist(interaction.user.id, interaction.user.roles):
            await interaction.response.send_message("Youre not authorized to use this command.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        formats = ParseJson.read_file("format.json")
        msg = f"**__Pokemon__**:\nTitle:```{formats['pokemon'][0]}```Description:```{formats['pokemon'][1]}```"
        msg += f"**__Raids__**:\nTitle:```{formats['raid'][0]}```Description:```{formats['raid'][1]}```"

        await interaction.followup.send(msg, ephemeral=True)

    @format_cmd.command(name="help", description="Info. about formatting. (Admin-Only)")
    async def format_help(self, interaction:discord.Interaction):
        if not Verification.verify_on_whitelist(interaction.user.id, interaction.user.roles):
            await interaction.response.send_message("Youre not authorized to use this command.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        desc_1 = "-The bot will attempt to replace anything surrounded by curly brakcets ({}) with the value they describe."
        desc_1 += "Ex: {lvl_val} --> 10\n-Use a \\n character to jump to a new line.\n"
        desc_1 += "-Surround words with '**' for bold.\n-Surround words with '__' for underline.\n"
        desc_1 += "-Surround words with '*' for italics."
        desc_1 += "-Use '/format reset' to reset formats to their default values.\n"
        desc_1 += "-Use '/format view' to see the current formats.\n"
        desc_1 += "-Use '/format set' to set a new format."
        
        desc_2 = "Pokemon Values:\n```{boosted},{iv},{atk_iv},{def_iv},{sta_iv},{cp},{lvl},{lvl_val},{ms},{move1},{move2},{star_cost_40},{star_cost_50},{candy_cost_40},{candy_cost_50},{xlcandy_cost_50},{star},{xl_candy},{location},{rare_candy},{pokemon_name},{gender},{expire_time}```\n"
        desc_2 += "Raid values:\n```{cp},{ms},{move1},{move2},{expire_time},{location},{team},{ex},{pokemon_name},{mega},{alignment},{gender}```"

        emb1 = discord.Embed(
                title="Format Help",
                description=desc_1,
                color=discord.Color.blue())
        emb2 = discord.Embed(title="Format Help contd.",
                description=desc_2,
                color=discord.Color.blue())
        await interaction.followup.send(embeds=[emb1,emb2], ephemeral=True)

    @format_cmd.command(name="reset", description="Reset format to default value. (Admin-Only)")
    async def format_reset(self, interaction:discord.Interaction):
        if not Verification.verify_on_whitelist(interaction.user.id, interaction.user.roles):
            await interaction.response.send_message("Youre not authorized to use this command.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        view = MenuView("reset")
        await interaction.followup.send(view=view, ephemeral=True)

    @format_cmd.command(name="set", description="Set a new format. (Admin-Only)")
    async def format_set(self, interaction:discord.Interaction):
        if not Verification.verify_on_whitelist(interaction.user.id, interaction.user.roles):
            await interaction.response.send_message("Youre not authorized to use this command.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        view = MenuView("set")
        await interaction.followup.send(view=view, ephemeral=True)


class MenuSelect(discord.ui.Select):
    def __init__(self, command_name):
        self.command_name = command_name
        self.format_options = [
                discord.SelectOption(label="Pokemon"),
                discord.SelectOption(label="Raid")
                ]
        command_info = {"reset":["Select choice to reset.",self.format_options],
                "set":["Select choice to modify.",self.format_options]}

        super().__init__(placeholder=command_info[self.command_name][0],
                min_values=1,
                max_values=1,
                options=command_info[self.command_name][1])

    async def callback(self, interaction: discord.Interaction):

        if self.command_name == "reset":
            await interaction.response.defer(ephemeral=True)
            choice = self.values[0].lower()

            default_formats = ParseJson.read_file("DEFAULT_FORMAT.json")
            user_formats = ParseJson.read_file("format.json")

            user_formats[choice][0] = default_formats[choice][0]
            user_formats[choice][1] = default_formats[choice][1]

            ParseJson.save_file("format.json", user_formats)

            await interaction.followup.send(f"`{choice}` Format reset.", ephemeral=True)

        if self.command_name == "set":
            choice = self.values[0].lower()
            await interaction.response.send_modal(FormatBox(choice))

class MenuView(discord.ui.View):
    def __init__(self, command):
        super().__init__()
        self.add_item(MenuSelect(command))

class FormatBox(discord.ui.Modal, title="Format"):
    def __init__(self, choice):
        super().__init__()
        self.choice = choice

    title_input = discord.ui.TextInput(
            label="Title Format",
            placeholder="Write your title format here.\n*{pokemon_name}* Ends: __{dsp}__",
            style=discord.TextStyle.long,
            required=False,
            max_length=200)

    format_input = discord.ui.TextInput(
            label="Description Format",
            placeholder="Write your format here.\n{iv}\\n{lvl} **{cp}**",
            style=discord.TextStyle.long,
            required=False,
            max_length=1500)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_formats = ParseJson.read_file("format.json")

        if self.title_input.value:
            user_formats[self.choice][0] = self.title_input.value
        if self.format_input.value:
            user_formats[self.choice][1] = self.format_input.value

        ParseJson.save_file("format.json", user_formats)

        await interaction.followup.send(f"`{self.choice}` Format Updated.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(GeneralCommands(bot))

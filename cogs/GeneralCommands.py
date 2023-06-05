import discord
from discord import app_commands
from discord.ext import commands
from discord.app_commands import Group
from discord.ext.commands import GroupCog
import asyncio
import logging

from utils.ParseJson import ParseJson
from utils.Verification import Verification
from utils.SSHUtils import SSHUtils
ParseJson = ParseJson()
Verification = Verification()
SSHUtils = SSHUtils()

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

    @rdm.command(name="update", description="Update RDM.")
    async def rdm_update(self, interaction:discord.Interaction):
        if not Verification.verify_owner(interaction.user.id):
            await interaction.response.send_message("You're not authorized to use this command.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        await interaction.followup.send("Beginning update. Please wait.", ephemeral=True)

        success = SSHUtils.rdm_update()

        if success[0]:
            output = success[1]
            if len(output) > 500:
                output = output[:500]
            for item in output:
                if "VersionManager" in output:
                    output = item
            await interaction.followup.send("RDM Updated.\n`{output}`", ephemeral=True)
        else:
            error = success[1]
            for item in error:
                if "up-to-date" in item:
                    error = "Already updated."
            await interaction.followup.send(f"Failed.\n`{error}`", ephemeral=True)


async def setup(bot):
    await bot.add_cog(GeneralCommands(bot))

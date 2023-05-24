PokeDB is a PokémonGo feed bot that queries data from your RDM database and parses it based on user input. From there it translates the data into a readable format and sends to a discord channel either in text or embed format.

PokeDB also has a webhook listener set up that takes data from external RDM services (ie: other mappers) and parses it in the same way as the other data. Additionally there are admin commands and toggles for most of these functions.

# Features

• Poke search

• Raid search

• Weather search

• Quest search

• Go Rocket search

• Track Pokémon spawns

• Track Raids

• Track in game weather

• Track only shiny Pokémon (only for accounts in rdm db)

• Assign pings to user(s) for shiny notifications 

• Switch between text format and embed format

• Whitelist channels

• Whitelist roles to use general commands

• Assign users admin controls

• Recieve external data from other mappers using webhook endpoints. You'll need to use ngrok for this 

# Requirements

## System

OS: >= Ubuntu 18

rdmdb

ngrok (Required if you plan on receiving data from external RDM databases)

## Python

Python Version: >= 3.8

discord.py==2.2.2

Flask==2.2.2

geopy==2.3.0

mysql_connector_repackaged==0.3.1

requests==2.22.0

# Configuration 

## Discord

The following steps must be taken:
- Create a new application on discord.
- Add a bot to the created application.
- Note the bot's token.
- Set up privileged gateway intents (presence intent, Server members intent, and message content intent)
- Invite the bot to your discord server.
- place the bot token into your `config.json` file
- Upload emojis as needed & place IDs in `utils > MsgUtils.py`

## Clone the Repo

Use `git clone git@github.com:spiri2/PokeDB.git`

## Bot Configuration

### /data/config.json

The main configuration file. Its format is displayed below. 

```{
"prefix":"enter_desired_prefix_here",
    "token":"enter_saved_token_here",
    "channel_whitelist":[integer_value,integer_value2,integer_value3],
    "psearch_embeds":[integer_value4,integer_value4,integer_value5],
    "role_whitelist":[integer_value5,integer_value6,integer_value7],
    "db_username":"rdm_database_username",
    "db_password":"rdm_database_password",
    "db_host":"rdm_database_ip_address",
    "db_name":"rdm_database_name",
    "db_tables":["rdm_database_pokemon_table_name1","rdm_database_pokemon_table_name2"] 
}```

The only fields that need to be configured manually are:
 - prefix
 - token
 - db_*
 
 ### /utils/verification.py

Line 6: `return user_id == YOUR_DISCORD_ID_HERE`

### /data/webhook_links.json (Optional)

Configuration file for custom webhook endpoints. The items inputted here will result in webhook endpoints like the following: `https://hostname.com/custom_endpoint`

Its format is displayed below:

```
["custom_endpoint","custom_endpoint2","custom_endpoint3"]
```
### /data/admin_whitelist.json

Configuration file for bot administrators. The items inputted here will result in a discord user being whitelisted as an admin and given access to all the bot's restricted commands.

Its format is displayed below:

```
[discord_userid,discord_userid2,discord_userid3]
```

### Discord Emote Configuration

Youll need to add the emote IDs from your server in `utils/MsgUtils.py`:

Weather emotes : `lines 26-32`

AR Emote : `line 105`

Pokestop Emote : `line 108`

Raid emotes : `lines 288-302`

Wild Spawn emotes : `lines 394-403`

Great/Ultra League Emote : `Lines 453-454`

Stats Emotes : `Lines 513-528`

# Starting Procedures

Three processes must be started for the bot to properly function:
- bot.py
- Hooks.py
- ngrok

## bot.py

`python bot.py`

## Hooks.py

`python Hooks.py`

## ngrok

`ngrok http 5000`

Or, if you're using a custom hostname:

`ngrok http --hostname=custom-hostname.com 5000`

# Commands

`<prefix>sync`

You must sync commands to your server prior to doing anything. 

`/pset <role> or <channel>`

Use this command to whitelist roles to use commands and whitelist channels for the commands to work.

`/toggle <embed>`

By default all messages will post in text format. You can switch to embed format or vice verse by using this command.

`/toggle ping`

This will ping the assigned discord user anytime a shiny Pokémon is found according to the username you input.

`ex: /toggle ping @InGameName @DiscordUser`

`/toggle admin add`

You can assign anyone admin rights using their discord ID.

`/toggle admin remove`

If someone has been naughty, remove their admin rights for the bot

`/psearch <name> <min_iv> <min_cp> <min_lvl>`

Search for Pokémon coordinates in your db. Pokémon name is required by default. iv, cp, and lvl are optional. 

`/rsearch <name> <tier>`

Search for raids with either the name or tier #

`/wsearch` 

This will provide a drop down menu: 

• Sunny

• Rainy

• Partly Cloudy

• Cloudy 

• Windy

• Snow

• Fog

If the data exists, it will post coordinates.

`/qsearch`

Search for Pokémon and item quests.

`/track Pokémon <name> <min_cp> <max_cp> <min_lvl> <max_lvl> <min_iv> <max_iv> <shiny_only>`

Plenty of options for you to choose from

`/track raid <name> <tier> <min_tier> <max_tier>`

Track raids by their name, individual tier #, or a range of tiers.

`/track weather`

This gives you a drop down menu similar to `/wsearch`.

Posting for weather tracking is every hour. You can change this by editing the value `in seconds` in `cogs > streams.py > change 3600 to whatever`

`/rocketsearch` 

This will provide a drop down menu: 

• Grunt

• Arlo

• Cliff

• Sierra 

• Giovanni

• Jessie

• James

`/untrack`

Removes the streams from the channel the command was used in.

`/stats`

Provides stats for pokemon data in a 24 hour period, provides the aevrage amount of pokemon data you get in a 7 day period, and provides account stats.

`/truncate`

This will provide a drop down menu that allows you to select a table to truncate within your RDM db: `account, devices, pokemon, quest, and weather` 

Note: This automatically disables foreign key check, truncates your selected table, then re-enables foreign key check. As an extra precaution, you will have to select either the confirm or cancel button to perform the actual truncate action. Consider this a "fat finger" safety measure.

More features are being added.

# Recieving Webhooks 

You can recieve webhook data in `json` format only by putting a unique string in the `data > webhook_links.json` file. This is taking into consideration you have your own domain and requires an ngrok account. 

# Support 

Visit the Discord server if you have any questions or need support: https://discord.gg/4rU2qu6KBY

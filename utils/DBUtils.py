import mysql.connector
from utils.ParseJson import ParseJson
import atexit
import time
import logging

ParseJson = ParseJson()
config = ParseJson.read_file("config.json")
table_names = config["db_tables"]

logging.basicConfig(level="WARNING")

class DBUtils:
    def __init__(self):
        self.items = ["pokemon_id","lat","lon","expire_timestamp","move_1","move_2","gender","cp",
                "iv","atk_iv","def_iv","sta_iv","form","level","weather","shiny","username","id","pvp",
                "is_ditto","display_pokemon_id"]
        self.raid_items = ["raid_pokemon_id","lat","lon","raid_end_timestamp","raid_pokemon_id","raid_level",
                "ex_raid_eligible","raid_pokemon_move_1","raid_pokemon_move_2","raid_pokemon_cp",
                "raid_pokemon_gender","id","name","team_id","raid_spawn_timestamp"]
        self.weather_items = ["id", "latitude", "longitude", "gameplay_condition"]
        self.quest_items = ["id","lat","lon","quest_timestamp","quest_title","quest_rewards",
                "quest_pokemon_id","ar_scan_eligible","quest_target","name"]
        self.incident_items = ["pokestop_id", "expiration", "`character`"]

    def get_cnx(self):
        cnx = mysql.connector.connect(
                user=config["db_username"],
                password=config["db_password"],
                host=config["db_host"],
                database=config["db_name"])
        return cnx

    def get_device_name(self, account_username):
        cnx = self.get_cnx()
        cursor = cnx.cursor()

        sql = "SELECT uuid FROM device WHERE account_username = %s"
        cursor.execute(sql, (account_username,))

        try:
            name = list(cursor)[0]
        except:
            name = [""]
        return name

    def query_id(self, pokemon_id, min_iv, min_cp, min_lvl):
        cnx = self.get_cnx()
        cursor = cnx.cursor()
        timestamp = time.time()+180
        results = []

        for table in table_names:
            if not pokemon_id:
                query = (f"""SELECT {','.join(self.items)} from {table} WHERE
                expire_timestamp > %s AND iv >= %s AND cp >= %s AND level >= %s""")
                cursor.execute(query, (timestamp, min_iv, min_cp, min_lvl))
            else:
                query = (f"""SELECT {','.join(self.items)} from {table} WHERE
                pokemon_id = %s AND expire_timestamp > %s AND iv >= %s AND cp >= %s AND level >= %s""")
                cursor.execute(query, (pokemon_id, timestamp, min_iv, min_cp, min_lvl))

            for pokemon in cursor:
                poke_dict = {}
                for key in self.items:
                    poke_dict[key] = pokemon[self.items.index(key)]
                results.append(poke_dict)

        cursor.close()
        cnx.close()
        return results
    
    def query_raid_id(self, pokemon_id, tier):
        cnx = self.get_cnx()
        cursor = cnx.cursor()
        timestamp = time.time()+180
        results = []

        values = [timestamp]
        query = f"""SELECT {','.join(self.raid_items)} FROM gym WHERE
        raid_end_timestamp > %s"""
        if pokemon_id:
            query += f""" AND raid_pokemon_id = %s"""
            values.append(pokemon_id)
        if tier != 0:
            query += f""" AND raid_level = %s"""
            values.append(tier)

        values = tuple(values)
        cursor.execute(query, values)

        for raids in cursor:
            raid_dict = {}
            for key in self.raid_items:
                raid_dict[key] = raids[self.raid_items.index(key)]
            results.append(raid_dict)
        
        cursor.close()
        cnx.close()
        return results

    def query_weather_id(self, weather_id):
        cnx = self.get_cnx()
        cursor = cnx.cursor()
        timestamp = time.time()-43200
        results = []

        values=[weather_id, timestamp]
        query = f"""SELECT {','.join(self.weather_items)} FROM weather WHERE
        gameplay_condition = %s AND updated > %s"""

        values = tuple(values)
        cursor.execute(query, values)

        for weather in cursor:
            weather_dict = {}
            for key in self.weather_items:
                weather_dict[key] = weather[self.weather_items.index(key)]
            results.append(weather_dict)

        cursor.close()
        cnx.close()
        return results

    def query_quest(self, user_query, field):
        cnx = self.get_cnx()
        cursor = cnx.cursor()
        results = []

        values=[user_query]
        query = f"""SELECT {','.join(self.quest_items)} FROM pokestop WHERE 
        {field} LIKE '{user_query}' """

        values = tuple(values)
        cursor.execute(query)

        for quest in cursor:
            quest_dict = {}
            for key in self.quest_items:
                quest_dict[key] = quest[self.quest_items.index(key)]
            results.append(quest_dict)

        cursor.close()
        cnx.close()
        return results

    def query_pokestops(self, pokestop_id_list):
        cnx = self.get_cnx()
        cursor = cnx.cursor()
        results = []

        query = f"""SELECT {','.join(self.quest_items)} FROM pokestop WHERE 
        id IN {tuple(pokestop_id_list)}"""
        cursor.execute(query)

        for quest in cursor:
            quest_dict = {}
            for key in self.quest_items:
                quest_dict[key] = quest[self.quest_items.index(key)]
            results.append(quest_dict)

        cursor.close()
        cnx.close()
        return results

    def query_leaders(self, leader_id):
        cnx = self.get_cnx()
        cursor = cnx.cursor()
        results = []
        expiration_timestamp = time.time()+600

        values = [expiration_timestamp, leader_id]

        query = f"""SELECT {','.join(self.incident_items)} FROM incident WHERE 
        expiration > %s AND `character` = %s"""
        if isinstance(leader_id, list):
            values = [expiration_timestamp]
            query = f"""SELECT {','.join(self.incident_items)} FROM incident WHERE
            expiration > %s AND `character` IN {tuple(leader_id)}"""

        values = tuple(values)
        cursor.execute(query, values)

        for leader in cursor:
            leader_dict = {}
            for key in self.incident_items:
                leader_dict[key] = leader[self.incident_items.index(key)]
            results.append(leader_dict)

        cursor.close()
        cnx.close()
        return results


    def stream_query(self, params):
        cnx = self.get_cnx()
        cursor = cnx.cursor()
        timestamp = time.time()+180
        value_list = [timestamp]
        results = []
        item_choices = {"pokemon":self.items,"gym":self.raid_items,"weather":self.weather_items}

        expire_timestamp = "expire_timestamp"
        if params["type"] == "gym":
            expire_timestamp = "raid_end_timestamp"

        query_msg = f"""SELECT {','.join(item_choices[params['type']])} FROM {params['type']} 
        WHERE {expire_timestamp} > %s AND """
        if params["type"] == "weather":
            del value_list[0]
            query_msg = f"""SELECT {','.join(item_choices[params['type']])} FROM {params['type']} 
            WHERE """

        for parameter in params:
            if parameter == "embed" or parameter == "type":
                continue
            value = params[parameter]
            if not value:
                continue
            if isinstance(value, list):
                query_msg += f"{parameter} >= %s AND {parameter} <= %s AND "
                value_list.extend(value)
                continue
            query_msg += f"{parameter} = %s AND "
            value_list.append(value)

        query_msg = query_msg[:-4]
        value_tuple = tuple(value_list)
        query = (query_msg)

        cursor.execute(query, value_tuple)

        for pokemon in cursor:
            poke_dict = {}
            for key in item_choices[params["type"]]:
                poke_dict[key] = pokemon[item_choices[params["type"]].index(key)]
            results.append(poke_dict)

        cursor.close()
        cnx.close()
        return results

    def insert_pokemon(self, value_list):
        cnx = self.get_cnx()
        cursor = cnx.cursor()

        for values in value_list:

            all_items = self.items.copy()
            all_items += ["expire_timestamp_verified","first_seen_timestamp"]
            values += [1,0]

            all_items.remove("iv")
            values.remove("IV_REMOVE")

            item_placeholder = ','.join(all_items)
            val_placeholder = "%s, "*(len(all_items)-1)
            val_placeholder += "%s"

            sql = f"""INSERT INTO pokemon ({item_placeholder})
            VALUES ({val_placeholder})"""

            try:
                cursor.execute(sql, values)
                cnx.commit()
            except Exception as e:
                print(e)
                pass

        cursor.close()
        cnx.close()

    def get_stats(self):
        cnx = self.get_cnx()
        cursor = cnx.cursor()

        pokemon_stats = {
                "pokemon_stats":[],
                "pokemon_hundo_stats":[],
                "pokemon_shiny_stats":[],
                "quest_stats":[],
                "invasion_stats":[],
                }
        account_stats = {
                "accounts_created":0,
                "accounts_leveled":0,
                "accounts_lvl0":0,
                "accounts_available":0,
                "accounts_in_use":0,
                "accounts_disabled":0,
                "accounts_warning":0,
                "accounts_failed":0
                }
        device_stats = []
        

        for stat_type in pokemon_stats:
            sql = f"SELECT SUM(count) FROM {stat_type} GROUP BY date"
            cursor.execute(sql)

            c_list = list(cursor)

            pokemon_stats[stat_type].append(int(c_list[-1][0]))

            days = 7
            if len(c_list) < 7:
                days = len(c_list)

            average = 0
            days_stats = c_list[len(c_list)-days:]
            for day in days_stats:
                average += day[0]
            average = int(average / days)

            pokemon_stats[stat_type].append(average)

        sql = f"SELECT username, level, last_disabled, failed, warn, banned, last_used_timestamp FROM account"
        cursor.execute(sql)

        for account in cursor:
            account = list(account)

            if account[0]:
                account_stats["accounts_created"] += 1
            if account[1] >= 30:
                account_stats["accounts_leveled"] += 1
            elif account[1] == 0:
                account_stats["accounts_lvl0"] += 1
            if account[2]:
                if ((time.time()-86400) < account[2]):
                    account_stats["accounts_disabled"] += 1
            if account[3]:
                account_stats["accounts_failed"] += 1
            if account[4]:
                account_stats["accounts_warning"] += 1
            if not account[2] and not account[3] and not account[4] and not account[5]:
                account_stats["accounts_available"] += 1

        sql = "SELECT uuid FROM device"
        cursor.execute(sql)

        accounts_used = len(list(cursor))
        account_stats["accounts_in_use"] = accounts_used
        account_stats["accounts_available"] -= accounts_used

        sql = "SELECT date FROM pokemon_hundo_stats"
        cursor.execute(sql)
        stats_time = list(cursor)[-1]

        sql = "SELECT uuid, instance_name, account_username, last_seen FROM device"
        cursor.execute(sql)
        for device in cursor:
            device_stats.append(
                {"uuid":device[0],
                "instance_name":device[1],
                "account_username":device[2],
                "last_seen":device[3]
                })

        cursor.close()
        cnx.close()
        return [pokemon_stats, account_stats, stats_time, device_stats]


    def truncate(self, table_name):
        cnx = self.get_cnx()
        cursor = cnx.cursor()

        sql = f"SET foreign_key_checks = 0; TRUNCATE TABLE {table_name}; SET foreign_key_checks = 1"
        try:
            cursor.execute(sql)
            cursor.close()
            cnx.close()
            return 1
        except Exception as e:
            cursor.close()
            cnx.close()
            return e

    def truncate_account(self, account_username):
        cnx = self.get_cnx()
        cursor = cnx.cursor()

        sql = f"DELETE FROM account WHERE username = '{account_username}'"
        try:
            cursor.execute(sql)
            cnx.commit()

            msg = f"<a:alert:1109202762987737179> Truncated: `{account_username}`"
        except Exception as e:
            msg = f"Failed.\n`{e}`"

        cursor.close()
        cnx.close()
        return msg

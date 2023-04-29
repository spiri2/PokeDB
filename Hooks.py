from flask import Flask, request
from utils.ParseJson import ParseJson
from utils.DBUtils import DBUtils
import json 

DBUtils = DBUtils()
ParseJson = ParseJson()
links = ParseJson.read_file("webhook_links.json")

app = Flask(__name__)

@app.route("/<hook_link>", methods=["POST"])
def receiver(hook_link):
    if hook_link not in links:
        return "Bad link.", 400

    try:
        data = request.data
        data = data.decode("utf-8").replace("'",'"')
        data = json.loads(data)
    except:
        return "Bad data.", 400

    if not isinstance(data, list):
        return "Bad data. Expecting list.", 400

    poke_list = []
    for info_dict in data:
        if "type" not in info_dict or info_dict["type"] != "pokemon":
            continue
        pokemon = info_dict["message"]

        data_keys = ["pokemon_id","latitude","longitude","disappear_time","move_1","move_2","gender",
                "cp","iv","individual_attack","individual_defense","individual_stamina",
                "form","pokemon_level","weather","shiny","username","encounter_id","pvp",
                "is_ditto","display_pokemon_id",]
        DB_keys = DBUtils.items

        if len(data_keys) != len(DB_keys):
            return "Database key error.", 500

        poke_values = []
        for pair in enumerate(DB_keys):
            ind = pair[0]
            key = pair[1]

            if key == "iv":
                poke_values.append("IV_REMOVE")
                continue
            if key == "is_ditto":
                poke_values.append((pokemon["pokemon_id"] == 132))
                continue
            if key == "pvp" and key in pokemon.keys() and pokemon[data_keys[ind]]:
                poke_values.append(str(pokemon[data_keys[ind]]).replace("'",'"'))
                continue

            try:
                poke_values.append(pokemon[data_keys[ind]])
            except Exception as e:
                continue

        if len(poke_values) != len(DB_keys):
            continue
        
        poke_list.append(poke_values)

    try:
        DBUtils.insert_pokemon(poke_list)
    except Exception as e:
        print(e)

    return "Ok", 200

if __name__ == "__main__":
    app.run()

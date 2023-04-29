from utils.ParseJson import ParseJson
ParseJson = ParseJson()

class Verification:
    def verify_YOUR-DISCORD-NAME-HERE(self, user_id):
        return user_id == YOUR-DISCORD-ID-HERE 

    def modify_whitelist(self, item_id, append=True):
        whitelist = ParseJson.read_file("admin_whitelist.json")
        if append:
            whitelist.append(item_id)
        else:
            try:
                whitelist.remove(item_id)
            except:
                return False

        ParseJson.save_file("admin_whitelist.json", whitelist)
        return True

    def verify_on_whitelist(self, user_id, user_roles):
        whitelist = ParseJson.read_file("admin_whitelist.json")

        for item_id in whitelist:
            if item_id == user_id:
                return True
            for role in user_roles:
                if role.id == item_id:
                    return True
        return False

import json
import os

data_directory = os.getcwd()+"/data/"

class ParseJson:
    def read_file(self, file_name):
        with open(data_directory+file_name) as json_file:
            data = json.load(json_file)
            return data
    def save_file(self, file_name, content):
        with open(data_directory+file_name, "w") as json_file:
            json.dump(content, json_file)
            return

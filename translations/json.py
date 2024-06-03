import json
import os


class MessageManager:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = self.load_data()

    # LOAD JSON DATA FROM translations.json

    def load_data(self):
        with open(self.file_path, "r", encoding="utf-8") as json_file:
            return json.load(json_file)

    # GET DESIRED TEXT BY KEYS

    def get_message(self, language, *keys, default_value=None):
        language_data = self.data.get(language, {})
        result = language_data

        for key in keys:
            result = result.get(key, {})

        if type(result) == list:
            return '\n'.join(result)

        else:
            return result if result else default_value


text = MessageManager(os.path.abspath('./translations/translations.json'))

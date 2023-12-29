import json
from pathlib import Path

import dynaconf

SETTINGS_PATH = Path(__file__).resolve().parent / 'settings.json'
SECRETS_PATH = Path(__file__).resolve().parent / '.secrets.toml'


class CustomDynaconf(dynaconf.Dynaconf):
    """Dynaconf class with method to save the changed settings"""

    def persist(self):
        # https://www.dynaconf.com/advanced/#exporting
        # loaders.write(self['SETTINGS_FILE_FOR_DYNACONF'][0], self.to_dict())
        with open(self['SETTINGS_FILE_FOR_DYNACONF'][0], 'w') as file:
            json.dump(self.to_dict(), file, indent=4)


settings = CustomDynaconf(
    settings_files=[
        SETTINGS_PATH,
        SECRETS_PATH
    ]
)

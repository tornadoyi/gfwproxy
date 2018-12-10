import os
import json



def save(config_file, content):
    # create config path
    os.makedirs(os.path.basename(config_file), exist_ok=True)

    # reset
    with open(config_file, 'w+') as f:
        json.dump(content, f)



def load(config_file):
    if not os.path.isfile(config_file): return {}
    with open(config_file, 'r') as f:
        return json.load(f)



def init(config_file, profile_path):
    _DEFAULT_CONTENT = {
        'mode': 'off',
        'profile': profile_path
    }

    # create config path
    os.makedirs(os.path.dirname(config_file), exist_ok=True)

    # reset
    with open(config_file, 'w+') as f:
        json.dump(_DEFAULT_CONTENT, f)
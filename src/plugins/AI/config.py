import tomllib
from pathlib import Path

rc=lambda role,content:{"role":role,"content":content}

BASE_DIR=Path(__file__).parent
CONFIG_PATH=BASE_DIR/"config.toml"

with open(CONFIG_PATH,"rb") as f:
    _data=tomllib.load(f)

ini=[rc("system",_data['personality']['default'])]
MODEL_NAME=_data['api']['model_name']
API_KEY=_data['api']['api_key']
TEMPERATURE=_data['api']['temperature']
GROUP_TRIGGERS=_data['triggers']['group_keywords']
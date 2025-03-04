import os
import os.path as osp
from tortoise import Tortoise

from core.constants import DATA_PATH

data_dir = osp.join(DATA_PATH, 'db')
os.makedirs(data_dir, exist_ok=True)
TIMEZONE = os.environ.get("TIMEZONE", "Asia/Shanghai")

TORTOISE_ORM = {
    "connections": {"default": f"sqlite://{data_dir}/db.sqlite3"},
    "apps": {
        "models": {
            "models": ["db.model"],
            "default_connection": "default",
        },
    },
    "use_tz": True,  # 启用时区支持
    "timezone": TIMEZONE,  # 设置时区
}


class DB:

    @staticmethod
    async def initialize():
        await Tortoise.init(config=TORTOISE_ORM)
        await Tortoise.generate_schemas()

    @staticmethod
    async def close():
        await Tortoise.close_connections()

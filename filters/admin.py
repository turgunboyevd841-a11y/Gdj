from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from config import config


class IsAdmin(BaseFilter):
    async def __call__(self, event: TelegramObject) -> bool:
        user = getattr(event, "from_user", None)
        return bool(user and user.id in config.admin_ids)
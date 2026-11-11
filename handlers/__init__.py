from aiogram import Router

from . import start
from . import xizmatlar
from . import buyurtma_qilish
from .admin import admin


def get_routers() -> list[Router]:
    return [
        admin.router,
        start.router,
        xizmatlar.router,
        buyurtma_qilish.router,
    ]
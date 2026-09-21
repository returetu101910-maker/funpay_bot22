import asyncio

from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message

from config import BOT_TOKEN
from database.storage import is_blocked
from handlers import start, profile, deals, admin, details, antilink


class BlockMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if isinstance(event, Message) and event.from_user:
            if is_blocked(event.from_user.id):
                return
        return await handler(event, data)


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    dp.message.middleware(BlockMiddleware())
    dp.callback_query.middleware(BlockMiddleware())

    dp.include_router(admin.router)
    dp.include_router(deals.router)
    dp.include_router(details.router)
    dp.include_router(profile.router)
    dp.include_router(antilink.router)
    dp.include_router(start.router)

    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

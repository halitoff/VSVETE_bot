import asyncio
import logging
import os

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from loguru import logger
from dotenv import load_dotenv
import json
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, ChatMemberUpdated

# Загружаем переменные из .env файла
load_dotenv()

# Получаем токен из переменных окружения
TOKEN = os.getenv("TOKEN")
ADMINS = {670698841, 6465381565}  # ID админов
logger.add("bot.log", level="INFO", rotation="1 MB")

bot = Bot(token=TOKEN)
dp = Dispatcher()
greet = ''

# Путь к файлу с состоянием бота
STATUS_FILE = "bot_status.json"


class MyStates(StatesGroup):
    waiting_for_response = State()


def read_greet_text():
    logger.success("Загрузка приветственного текста успешна!")
    with open("greet.txt", "r", encoding="utf-8") as f:
        return f.read()


def truncate_greet_text():
    with open("greet.txt", "r+") as file:
        file.seek(0)  # Перемещаем указатель в начало файла
        file.truncate()  # Обрезаем файл до текущей позиции (0 байт)
    logger.warning("Приветственный текст очищен!")


def write_greet_text(text: str):
    if "%username" not in text:
        logger.error("❌ Ключ %username отсутствует в тексте!")
        return False
    truncate_greet_text()
    text = text.replace("%username", "%s")
    with open("greet.txt", "w", encoding="utf-8") as f:
        f.write(text)
    return True


# Функция для чтения статуса из файла
def get_status():
    try:
        with open(STATUS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"status": "⚠️ Статус недоступен"}


# Функция для записи статуса в файл
def update_status(status):
    with open(STATUS_FILE, "w") as f:
        json.dump({"status": status}, f)


@dp.message(Command("status"))
async def check_status(message: Message):
    if message.from_user.id in ADMINS:
        status = get_status()
        await message.answer(status["status"])

    else:
        await message.answer("❌ У вас нет прав на эту команду!")

# Функция для обработки команды /new_greet_message
@dp.message(Command("new_greet_message"))
async def check_status(message: Message, state: FSMContext):
    if message.chat.id < 0:
        return
    print(message.chat.id, type(message.chat.id))
    await message.answer("Напиши что-нибудь и я обновлю приветственный текст!")
    await state.set_state(MyStates.waiting_for_response)



@dp.message(MyStates.waiting_for_response)
async def process_name(message: Message, state: FSMContext):
    global greet
    logger.info("Получен текст: %s" % message.text)
    result = write_greet_text(message.text)
    if result:
        await message.answer("✅ Приветственный текст обновлен!")
        logger.success("✅ Приветственный текст обновлен!")
        greet = read_greet_text()
    else:
        await message.answer("❌ Приветственный текст не обновлен!")
        logger.error("❌ Приветственный текст не обновлен!")
    await state.clear()


@dp.chat_member()
async def greet_new_member(update: ChatMemberUpdated):
    if update.new_chat_member.status == "member":  # Проверяем, что участник присоединился
        logger.info(
            f"Новый участник: {update.new_chat_member.user.full_name} - @{update.new_chat_member.user.username}\n")
        chat_id = update.chat.id
        user = update.new_chat_member.user
        await bot.send_message(chat_id, greet % user.full_name if user.full_name else user.username)
        logger.success(f"Участник {user.full_name} присоединился к чату {chat_id}!")
    else:
        logger.warning(f"Участник {update.new_chat_member.user.full_name} покинул чат")


@logger.catch
async def main():
    logger.success("✅ Бот работает нормально!")
    update_status("✅ Бот работает нормально!")  # Начальный статус
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"⚠️ Бот упал: {str(e)}")
        update_status(f"⚠️ Бот упал: {str(e)}")  # Обновляем статус при падении
        logging.error(e)
        raise e


if __name__ == "__main__":
    greet = read_greet_text()
    logger.info("Приветственный текст: %s" % greet)
    asyncio.run(main())

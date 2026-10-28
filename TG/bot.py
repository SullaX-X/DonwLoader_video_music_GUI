import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from core import DownloadEngine
from utils import resource_path

# Вставь сюда свой токен от BotFather
API_TOKEN = 'ТВОЙ_ТОКЕН_ТУТ'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
# Используем None для прогресс-хука, так как в боте он будет другой
engine = DownloadEngine(progress_hook=lambda d: None)


@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "👋 Привет! Я Media Downloader Bot.\n\n"
        "Отправь мне ссылку на YouTube, Instagram или TikTok,\n"
        "и я пришлю тебе аудио или видео!\n\n"
        "Используй кнопки ниже для выбора режима."
    )


@dp.message(F.text.startswith("http"))
async def handle_link(message: types.Message):
    url = message.text
    status_msg = await message.answer("⏳ Начинаю загрузку... Пожалуйста, подождите.")

    save_dir = "bot_downloads"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    try:
        # Для начала сделаем просто скачивание аудио (MP3)
        # В будущем можно добавить кнопки выбора формата
        file_path = await asyncio.to_thread(engine.download_for_bot, url, False, save_dir)

        await status_msg.edit_text("✅ Скачивание завершено! Отправляю файл...")

        # Отправляем файл пользователю
        audio_file = types.FSInputFile(file_path)
        await message.answer_audio(audio_file, caption="С любовью от SullaX_X и ParsifalX_X")

        # Удаляем файл с сервера после отправки, чтобы не забивать место
        os.remove(file_path)
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка: {str(e)}")


async def main():
    print("Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

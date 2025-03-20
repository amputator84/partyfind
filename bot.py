import logging
import asyncio
from aiogram import Bot, Router, types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
import csv

API_TOKEN = '7836408224:AAGTTxfnvX8VYrq6WEnOE8Vdzfj5rbwT0cM'

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
router = Router()

def extract_unique_cities(file_path):
    cities = set()  # Используем множество для хранения уникальных городов
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=';')  # Читаем CSV с разделителем ';'
        for row in reader:
            city = row['city'].strip()  # Убираем лишние пробелы
            if city:  # Проверяем, что город не пустой
                cities.add(city)  # Добавляем город в множество
    
    # Упорядочиваем города в алфавитном порядке
    sorted_cities = sorted(cities, key=lambda x: x.lower())  # Сортируем без учета регистра
    return sorted_cities  # Возвращаем отсортированный список городов

cities = extract_unique_cities('events.csv')

def cities_menu():
    upper_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1a", callback_data="s15"),
            InlineKeyboardButton(text="2s", callback_data="s25"),
            InlineKeyboardButton(text="3a3", callback_data="s35"),
            InlineKeyboardButton(text="4s", callback_data="s45"),
        ]
    ])
    return upper_keyboard.inline_keyboard

def cities_menu2(page=0, per_page=3):
    keyboard = []
    start = page * per_page
    end = start + per_page

    # Проверяем, есть ли предыдущая страница
    if page > 0:
        keyboard.append(InlineKeyboardButton("<<", callback_data=f"page_{page - 1}"))

    # Добавляем города на текущей странице
    for city in cities[start:end]:
        keyboard.append(InlineKeyboardButton(city, callback_data=f"city_{city}"))

    # Если это последняя страница и остались города
    if end >= len(cities) and start < len(cities):
        remaining_cities = cities[end:]
        for city in remaining_cities:
            keyboard.append(InlineKeyboardButton(city, callback_data=f"city_{city}"))

    # Проверяем, есть ли следующая страница
    if end < len(cities):
        keyboard.append(InlineKeyboardButton(">>", callback_data=f"page_{page + 1}"))

    return keyboard

# Общее меню
bottom_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="Домой", callback_data="start"),
        InlineKeyboardButton(text="Поиск города", callback_data="get_city"),
        InlineKeyboardButton(text="Города СФО", callback_data="get_cities_from_db"),
        InlineKeyboardButton(text="Помощь", callback_data="help")
    ]
]).inline_keyboard

def get_upper_keyboard():
    upper_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1", callback_data="s1"),
            InlineKeyboardButton(text="2", callback_data="s2"),
            InlineKeyboardButton(text="33", callback_data="s3"),
            InlineKeyboardButton(text="4", callback_data="s4"),
        ]
    ])
    return upper_keyboard.inline_keyboard

# Меню событий для города
#def events_menu(city):
#    keyboard = [
#        InlineKeyboardButton(f"Тусы недели города {city}", callback_data=f"get_events_week_{city}"),
#        InlineKeyboardButton(f"Все тусы города {city}", callback_data=f"get_events_all_{city}")
#    ]
#    return keyboard

# Команда /start
@router.message(Command('start'))
async def send_start(message: types.Message):
    combined_markup = InlineKeyboardMarkup(inline_keyboard=get_upper_keyboard() + bottom_keyboard)
    await message.answer("Добро пожаловать! Выберите опцию:", reply_markup=combined_markup)


# Обработчик нажатия на кнопку "Домой"
@router.callback_query(lambda c: c.data == 'start')
async def call_start(callback_query: types.CallbackQuery):
    combined_markup = InlineKeyboardMarkup(inline_keyboard=get_upper_keyboard() + bottom_keyboard)
    await callback_query.message.edit_text("Добро пожаловать! Выберите опцию:", reply_markup=combined_markup)

# Обработчик нажатия на кнопку "Домой"
@router.callback_query(lambda c: c.data == 'get_cities_from_db')
async def get_cities_from_db(callback_query: types.CallbackQuery):
    print('get_cities_from_db')
    #combined_markup = InlineKeyboardMarkup(inline_keyboard=get_two_keyboard() + bottom_keyboard)
    keyboard = InlineKeyboardMarkup(inline_keyboard=cities_menu() + bottom_keyboard)
    await callback_query.message.edit_text("Выберите город из списка", reply_markup=keyboard)

# Запуск бота
async def main():
    dp = Dispatcher(storage=storage)
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
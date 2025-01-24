import csv
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
import asyncio

API_TOKEN = '123'

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Функция для чтения CSV файла
def read_csv(file_path):
    events = []
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=';')
        for row in reader:
            events.append(row)
    return events

# Функция для группировки и сортировки событий
def group_events_by_weekday(events, city, week):
    filtered_events = [event for event in events if event['city'].lower() == city.lower()]
    for event in filtered_events:
        event['start_date'] = datetime.strptime(event['start_date'], '%d.%m.%Y')

    if week == 1:
        today = datetime.utcnow()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)  # Конец недели
        filtered_events = [event for event in filtered_events if start_of_week <= event['start_date'] <= end_of_week]

    grouped_events = {}
    for event in filtered_events:
        weekday = event['start_date'].strftime('%A')
        if weekday not in grouped_events:
            grouped_events[weekday] = []
        grouped_events[weekday].append(event)

    return grouped_events

# Функция для формирования сообщения
def format_message(grouped_events):
    weekdays_russian = {
        'Monday': 'Понедельник',
        'Tuesday': 'Вторник',
        'Wednesday': 'Среда',
        'Thursday': 'Четверг',
        'Friday': 'Пятница',
        'Saturday': 'Суббота',
        'Sunday': 'Воскресенье'
    }
    
    message_parts = []
    for weekday, events in grouped_events.items():
        message_parts.append(f"{weekdays_russian[weekday]} {events[0]['start_date'].strftime('%d.%m.%Y')}")
        for event in events:
            #message_parts.append(f"{event['name']} ({event['screen_name_link']})")
            message_parts.append(f"[{event['name']}](https://vk.com/{event['screen_name_link']})")
            # f"[{event[1]}](https://vk.com/{event[2]})\n"
        message_parts.append("")  # Добавляем пустую строку для разделения

    return "\n".join(message_parts).strip()

@dp.message_handler(commands=['events'])
async def send_events(message: types.Message):
    city = message.get_args().split()[0]  # Получаем город из аргументов команды
    week = int(message.get_args().split()[1]) if len(message.get_args().split()) > 1 else 0

    events = read_csv('events.csv')  # Укажите путь к вашему CSV файлу
    grouped_events = group_events_by_weekday(events, city, week)
    formatted_message = format_message(grouped_events)

    # Разделяем сообщение, если оно превышает 4096 символов
    if len(formatted_message) > 4096:
        # Разбиваем сообщение по строкам
        message_parts = formatted_message.split('\n')
        current_part = ""
        
        for line in message_parts:
            # Проверяем, если добавление строки не превышает лимит
            if len(current_part) + len(line) + 1 <= 4096:  # +1 для символа новой строки
                current_part += line + '\n'
            else:
                # Отправляем текущую часть и начинаем новую
                await message.answer(current_part.strip(), parse_mode="Markdown", disable_web_page_preview=True)
                current_part = line + '\n'  # Начинаем новую часть с текущей строки
        
        # Отправляем оставшуюся часть
        if current_part:
            await message.answer(current_part.strip(), parse_mode="Markdown", disable_web_page_preview=True)
    else:
        await message.answer(formatted_message, parse_mode="Markdown", disable_web_page_preview=True)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
from aiogram import Bot, Router, types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.storage.memory import MemoryStorage
import csv
import requests
import asyncio

# Bot and API tokens
API_TOKEN = '123'
vkToken = '321'
vkApi = '5.131'
file_path = 'events.csv'

# Initialize bot and storage
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
router = Router()

day_of_week_rus = {
    'Monday': 'Понедельник',
    'Tuesday': 'Вторник',
    'Wednesday': 'Среда',
    'Thursday': 'Четверг',
    'Friday': 'Пятница',
    'Saturday': 'Суббота',
    'Sunday': 'Воскресенье'
}
def get_city(city):
    response = requests.get(
        'https://api.vk.com/method/database.getCities',
        params={
            'access_token': vkToken,
            'v': vkApi,
            'country_id': 1,  # ID страны (1 - Россия)
            'q': city,
            'count': 1
        }
    )
    try:
        data = response.json()
        if 'response' in data and 'items' in data['response'] and len(data['response']['items']) > 0:
            return data['response']['items'][0]
        else:
            return ''
    except Exception as e:
        print(f"Ошибка {e}")
        
def get_group_info(group_ids):
    group_info = []
    for i in range(0, len(group_ids), 500):
        groupIds = ','.join(group_ids[i:i + 500])
        url = f"https://api.vk.com/method/groups.getById/?group_ids={groupIds}&fields=start_date,finish_date,description,city&access_token={vkToken}&v={vkApi}"
        response = requests.get(url)
        data = response.json()
        if 'response' in data:
            group_info.extend(data['response'])
        time.sleep(1)
    return group_info

def get_info_from_groups(groups, week):
    events_by_date = defaultdict(list)
    unique_events = set()
    for event in groups:
        try:
            start_date = event.get('start_date')
            today = datetime.now()
            if start_date and start_date > int(today.timestamp()):
                start_date_dt = datetime.fromtimestamp(start_date)
                start_date_formatted = start_date_dt.strftime('%d.%m.%Y')
                day_of_week = start_date_dt.strftime('%A')
                screen_name_link = event.get('screen_name')
                name = event.get('name', '').replace('[', ' ').replace(']', ' ').replace('{', ' ').replace('}', ' ').replace('|', ' ')
                event_id = (screen_name_link, name)

                if week == 1:
                    start_of_week = today - timedelta(days=today.weekday())
                    end_of_week = start_of_week + timedelta(days=6)
                    if start_of_week <= start_date_dt <= end_of_week and event_id not in unique_events:
                        unique_events.add(event_id)
                        events_by_date[start_date_formatted].append((day_of_week, name, screen_name_link))
                else:
                    if event_id not in unique_events:
                        unique_events.add(event_id)
                        events_by_date[start_date_formatted].append((day_of_week, name, screen_name_link))
        except Exception as e:
            print(f"Ошибка при обработке события: {e}")
    message_parts = []
    for date in sorted(events_by_date.keys(), key=lambda x: datetime.strptime(x, '%d.%m.%Y')):
        day_of_week = day_of_week_rus[events_by_date[date][0][0]]
        message_parts.append(f"{day_of_week} {date}")
        for event in events_by_date[date]:
            message_parts.append(f"[{event[1]}](https://vk.com/{event[2]})")
        message_parts.append("")
    formatted_message = "\n".join(message_parts).strip()
    messages = []
    if len(formatted_message) > 4096:
        message_parts = formatted_message.split('\n')
        current_part = ""
        for line in message_parts:
            if len(current_part) + len(line) + 1 <= 4096:
                current_part += line + '\n'
            else:
                messages.append(current_part.strip())
                current_part = line + '\n'
        if current_part:
            messages.append(current_part.strip())
    else:
        messages.append(formatted_message)

    return messages

def get_events(city_id):
    arrLinkVkAll = []
    for word in arrWord:
        urlAll = f"https://api.vk.com/method/groups.search/?q={word}&type=event&city_id={city_id}&future=1&offset=0&count=999&access_token={vkToken}&v={vkApi}"
        print(f"Запрос URL: {urlAll}")
        response = requests.get(urlAll)
        data = response.json()
        if 'response' in data and 'items' in data['response']:
            for event in data['response']['items']:
                arrLinkVkAll.append(event['screen_name'])
        time.sleep(0.5)
    return arrLinkVkAll

def extract_unique_cities(file_path):
    cities = set()
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=';')
        for row in reader:
            city = row['city'].strip()
            if city:
                cities.add(city)
    sorted_cities = sorted(cities, key=lambda x: x.lower())
    return sorted_cities

cities = extract_unique_cities('events.csv')

def main_menu(arr = 0):
    #if arr == 0:
    #    keyboard = InlineKeyboardMarkup(row_width=4)
    #    keyboard.add(
    #        InlineKeyboardButton("Домой", callback_data="start"),
    #        InlineKeyboardButton("Поиск города", callback_data="get_city"),
    #        InlineKeyboardButton("Города СФО", callback_data="get_cities_from_db"),
    #        InlineKeyboardButton("Помощь", callback_data="help")
    #    )
    #else:
    #    keyboard = [InlineKeyboardButton("Домой", callback_data="start"),
    #                InlineKeyboardButton("Поиск города", callback_data="get_city"),
    #                InlineKeyboardButton("Города СФО", callback_data="get_cities_from_db"),
    #                InlineKeyboardButton("Помощь", callback_data="help")]
    #return keyboard
    builder = InlineKeyboardBuilder()
    builder.button(text="Домой", callback_data="start")
    builder.button(text="Поиск города", callback_data="get_city")
    builder.button(text="Города СФО", callback_data="get_cities_from_db")
    builder.button(text="Помощь", callback_data="help")
    return builder

def cities_menu(page=0, per_page=3):
    builder = InlineKeyboardBuilder()
    start = page * per_page
    end = start + per_page

    if page > 0:
        builder.button(text="<<", callback_data=f"page_{page - 1}")

    for city in cities[start:end]:
        builder.button(text=city, callback_data=f"city_{city}")

    if end < len(cities):
        builder.button(text=">>", callback_data=f"page_{page + 1}")

    return builder

def events_menu(city):
    #keyboard = [
    #    InlineKeyboardButton(f"Тусы недели города {city}", callback_data=f"get_events_week_{city}"),
    #    InlineKeyboardButton(f"Все тусы города {city}", callback_data=f"get_events_all_{city}")
    #]
    #return keyboard
    builder = InlineKeyboardBuilder()
    
    # Начинаем новый ряд для нижнего меню
    builder.row()
    
    # Добавляем 3 кнопки в нижний ряд
    builder.button(text=f"Тусы недели города {city}", callback_data=f"get_events_week_{city}")
    builder.button(text=f"Все тусы города {city}", callback_data=f"get_events_all_{city}")
    
    return builder

@router.message(Command('start'))
async def start_command(message: types.Message):
    await message.answer("Добро пожаловать! Выберите опцию:", reply_markup=main_menu().as_markup())

@router.message(Command('help'))
async def help_command(message: types.Message):
    await message.answer("Тут будет хэлпник", reply_markup=main_menu().as_markup())

@router.message(Command('get_city'))
async def get_city_command(message: types.Message):
    await message.answer("Введите название города", reply_markup=main_menu().as_markup())

@router.message(Command('get_cities_from_db'))
async def get_cities_from_db_command(message: types.Message):
    #keyboard = InlineKeyboardMarkup(inline_keyboard=[cities_menu(), main_menu(1)])
    top_menu = cities_menu()
    bottom_menu = main_menu(1)
    keyboard = InlineKeyboardBuilder()
    keyboard.add(*top_menu.inline_keyboard)
    keyboard.add(*bottom_menu.inline_keyboard)
    combined_menu = InlineKeyboardBuilder()
    combined_menu.add(*top_menu.as_markup().inline_keyboard[0])
    combined_menu.add(*bottom_menu.as_markup().inline_keyboard[0])
    await message.answer("Выберите город из списка:", reply_markup=combined_menu.as_markup())

@router.callback_query(lambda c: True)
async def process_callback(callback_query: types.CallbackQuery):
    data = callback_query.data

    if data == "start":
        await callback_query.message.edit_text("Добро пожаловать! Выберите опцию:", reply_markup=main_menu().as_markup())
    elif data == "get_city":
        await callback_query.message.edit_text("Введите название города", reply_markup=main_menu().as_markup())
    elif data == "get_cities_from_db":
        #keyboard = InlineKeyboardMarkup(inline_keyboard=[cities_menu(), main_menu(1)])
        top_menu = cities_menu()
        bottom_menu = main_menu(1)
        keyboard = InlineKeyboardBuilder()
        keyboard.add(*top_menu.inline_keyboard)
        keyboard.add(*bottom_menu.inline_keyboard)
        combined_menu = InlineKeyboardBuilder()
        combined_menu.add(*top_menu.as_markup().inline_keyboard[0])
        combined_menu.add(*bottom_menu.as_markup().inline_keyboard[0])
        await callback_query.message.edit_text("Выберите город из списка:", reply_markup=combined_menu.as_markup())
    elif data == "help":
        await callback_query.message.edit_text("Тут будет хэлпник", reply_markup=main_menu().as_markup())
    elif data.startswith("page_"):
        page = int(data.split("_")[1])
        #keyboard = InlineKeyboardMarkup(inline_keyboard=[cities_menu(page=page), main_menu(1)])
        top_menu = cities_menu(page=page)
        bottom_menu = main_menu(1)
        keyboard = InlineKeyboardBuilder()
        keyboard.add(*top_menu.inline_keyboard)
        keyboard.add(*bottom_menu.inline_keyboard)
        combined_menu = InlineKeyboardBuilder()
        combined_menu.add(*top_menu.as_markup().inline_keyboard[0])
        combined_menu.add(*bottom_menu.as_markup().inline_keyboard[0])
        await callback_query.message.edit_text("Выберите город из списка:", reply_markup=combined_menu.as_markup())
    elif data.startswith("city_"):
        city = data.split("_")[1]
        if city in cities:
            #keyboard = InlineKeyboardMarkup(inline_keyboard=[events_menu(city),main_menu(1)])
            top_menu = events_menu(city)
            bottom_menu = main_menu(1)
            keyboard = InlineKeyboardBuilder()
            keyboard.add(*top_menu.inline_keyboard)
            keyboard.add(*bottom_menu.inline_keyboard)
            combined_menu = InlineKeyboardBuilder()
            combined_menu.add(*top_menu.as_markup().inline_keyboard[0])
            combined_menu.add(*bottom_menu.as_markup().inline_keyboard[0])
            await callback_query.message.edit_text(f"Тусы {city} уже есть. Выберите опцию:", reply_markup=combined_menu.as_markup())
        else:
            await callback_query.message.edit_text("Введите другой город", reply_markup=main_menu().as_markup())
    elif data.startswith("get_events_week_"):
        city = data.split("_")[3]
        #keyboard = InlineKeyboardMarkup(inline_keyboard=[events_menu(city), main_menu(1)])
        top_menu = events_menu(city)
        bottom_menu = main_menu(1)
        keyboard = InlineKeyboardBuilder()
        keyboard.add(*top_menu.inline_keyboard)
        keyboard.add(*bottom_menu.inline_keyboard)
        combined_menu = InlineKeyboardBuilder()
        combined_menu.add(*top_menu.as_markup().inline_keyboard[0])
        combined_menu.add(*bottom_menu.as_markup().inline_keyboard[0])
        if city in cities:
            grouped_events = get_events_from_csv(city, 1)
            if (grouped_events[0] == ''):
                await callback_query.message.edit_text(f"Для города {city} нет тус недели, попробуй выбери \"Все тусы\"", reply_markup=combined_menu.as_markup(), parse_mode="Markdown",disable_web_page_preview=True)
            if (len(grouped_events) == 1 and grouped_events[0] != ''):
                await callback_query.message.edit_text(f"Это тусы недели для города {city} \n {grouped_events[0]}", reply_markup=combined_menu.as_markup(), parse_mode="Markdown",disable_web_page_preview=True)
            else:
                i = 0
                head = ''
                for message in grouped_events:
                    if i == 0:
                        head = f"{city}\n\n"
                    else:
                        head = ''
                    await bot.send_message(callback_query.from_user.id, message, parse_mode="Markdown",disable_web_page_preview=True)
                    i = i + 1
                await bot.send_message(callback_query.from_user.id, f"Выше тусы недели для города {city}", reply_markup=combined_menu.as_markup(), parse_mode="Markdown",disable_web_page_preview=True)
        else:
            city = get_city(city)
            city_id = city['id']
            city_title = city['title']
            await callback_query.message.edit_text(f"Ожидайте, идёт сбор тус по городу {city_title}", disable_web_page_preview=True)
            events = get_events(city_id)
            groups = get_group_info(events)
            events_from_groups = get_info_from_groups(groups, 1)
            if (events_from_groups[0] == ''):
                await callback_query.message.edit_text(f"Для города {city_title} нет тус недели, попробуй выбери \"Все тусы\"", reply_markup=combined_menu.as_markup(), parse_mode="Markdown",disable_web_page_preview=True)
            if (len(events_from_groups) == 1 and events_from_groups[0] != ''):
                await callback_query.message.edit_text(f"Это тусы недели для города {city_title} \n {events_from_groups[0]}", reply_markup=combined_menu.as_markup(), parse_mode="Markdown",disable_web_page_preview=True)
            else:
                i = 0
                head = ''
                for message in events_from_groups:
                    if i == 0:
                        head = f"{city_title}\n\n"
                    else:
                        head = ''
                    await bot.send_message(callback_query.from_user.id, message, parse_mode="Markdown",disable_web_page_preview=True)
                    i = i + 1
                await bot.send_message(callback_query.from_user.id, f"Это тусы недели для города {city_title}", reply_markup=combined_menu.as_markup(), parse_mode="Markdown",disable_web_page_preview=True)
    # Все тусы города
    elif data.startswith("get_events_all_"):
        city = data.split("_")[3]
        grouped_events = get_events_from_csv(city, 0)
        #keyboard = InlineKeyboardMarkup(inline_keyboard=[events_menu(city), main_menu(1)])
        top_menu = events_menu(city)
        bottom_menu = main_menu(1)
        keyboard = InlineKeyboardBuilder()
        keyboard.add(*top_menu.inline_keyboard)
        keyboard.add(*bottom_menu.inline_keyboard)
        combined_menu = InlineKeyboardBuilder()
        combined_menu.add(*top_menu.as_markup().inline_keyboard[0])
        combined_menu.add(*bottom_menu.as_markup().inline_keyboard[0])
        if city in cities:
            if (grouped_events[0] == ''):
                await callback_query.message.edit_text(f"Для города {city} нет тус недели, попробуй выбери \"Все тусы\"", reply_markup=combined_menu.as_markup(), parse_mode="Markdown",disable_web_page_preview=True)
            if (len(grouped_events) == 1 and grouped_events[0] != ''):
                await callback_query.message.edit_text(f"Это все тусы для города {city} \n {grouped_events[0]}", reply_markup=combined_menu.as_markup(), parse_mode="Markdown",disable_web_page_preview=True)
            else:
                i = 0
                head = ''
                for message in grouped_events:
                    if i == 0:
                        head = f"{city}\n\n"
                    else:
                        head = ''
                    await bot.send_message(callback_query.from_user.id, head + message, parse_mode="Markdown",disable_web_page_preview=True)
                    i = i + 1
                await bot.send_message(callback_query.from_user.id, f"Выше все тусы для города {city}", reply_markup=combined_menu.as_markup(), parse_mode="Markdown",disable_web_page_preview=True)
        else:
            city = get_city(city)
            city_id = city['id']
            city_title = city['title']
            events = get_events(city_id)
            groups = get_group_info(events)
            events_from_groups = get_info_from_groups(groups, 0)
            if (events_from_groups[0] == ''):
                await callback_query.message.edit_text(f"Для города {city_title} нет тус", reply_markup=combined_menu.as_markup(), parse_mode="Markdown",disable_web_page_preview=True)
            elif (len(events_from_groups) == 1 and events_from_groups[0] != ''):
                await callback_query.message.edit_text(f"Это все тусы для города {city_title} \n {events_from_groups[0]}", reply_markup=combined_menu.as_markup(), parse_mode="Markdown",disable_web_page_preview=True)
            else:
                i = 0
                head = ''
                for message in events_from_groups:
                    if i == 0:
                        head = f"{city_title}\n\n"
                    else:
                        head = ''
                    await bot.send_message(callback_query.from_user.id, head + message, parse_mode="Markdown",disable_web_page_preview=True)
                    i = i + 1
                await bot.send_message(callback_query.from_user.id, f"Выше все тусы для города {city_title}", reply_markup=keyboard.as_markup(), parse_mode="Markdown",disable_web_page_preview=True)

@router.message(lambda message: True)
async def get_text(message: types.Message):
    if message.text in cities:  # Проверяем, есть ли город в массиве
        #keyboard = InlineKeyboardMarkup(inline_keyboard=[events_menu(message.text),main_menu(1)])
        top_menu = events_menu(city)
        bottom_menu = main_menu(1)
        keyboard = InlineKeyboardBuilder()
        keyboard.add(*top_menu.inline_keyboard)
        keyboard.add(*bottom_menu.inline_keyboard)
        combined_menu = InlineKeyboardBuilder()
        combined_menu.add(*top_menu.as_markup().inline_keyboard[0])
        combined_menu.add(*bottom_menu.as_markup().inline_keyboard[0])
        await message.answer(f"Тусы {message.text} уже есть. Выберите опцию:", reply_markup=combined_menu.as_markup())
    else:
        # ищем город в ВК. Если не нашли, сообщение
        city = get_city(message.text)
        if city == '':
            city_id = ''
            city_title = ''
        else:
            city_id = city['id']
            city_title = city['title']
        
        if city_id == '':
            await message.answer("Не нашли такого города, введите другой", reply_markup=main_menu().as_markup())
        else:
            #keyboard = InlineKeyboardMarkup(inline_keyboard=[events_menu(city_title),main_menu(1)])
            top_menu = events_menu(city)
            bottom_menu = main_menu(1)
            keyboard = InlineKeyboardBuilder()
            keyboard.add(*top_menu.inline_keyboard)
            keyboard.add(*bottom_menu.inline_keyboard)
            combined_menu = InlineKeyboardBuilder()
            combined_menu.add(*top_menu.as_markup().inline_keyboard[0])
            combined_menu.add(*bottom_menu.as_markup().inline_keyboard[0])
            await message.answer(f"Город {city_title} найден. Выберите опцию:", reply_markup=combined_menu.as_markup())

# Функция для чтения CSV файла
def read_csv(file_path):
    events = []
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=';')
        for row in reader:
            events.append(row)
    return events

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

def format_message(grouped_events):    
    message_parts = []
    for weekday, events in grouped_events.items():
        message_parts.append(f"{day_of_week_rus[weekday]} {events[0]['start_date'].strftime('%d.%m.%Y')}")
        for event in events:
            message_parts.append(f"[{event['name']}](https://vk.com/{event['screen_name_link']})")
        message_parts.append("")
    
    formatted_message = "\n".join(message_parts).strip()
    messages = []

    if len(formatted_message) > 4096:
        message_parts = formatted_message.split('\n')
        current_part = ""
        for line in message_parts:
            if len(current_part) + len(line) + 1 <= 4096:
                current_part += line + '\n'
            else:
                messages.append(current_part.strip())
                current_part = line + '\n'
        if current_part:
            messages.append(current_part.strip())
    else:
        messages.append(formatted_message)
    return messages

def get_events_from_csv(city, week):
    events = read_csv('events.csv')
    grouped_events = group_events_by_weekday(events, city, week)
    formatted_message = format_message(grouped_events)
    return formatted_message

# Run the bot
async def main():
    print('main')
    dp = Dispatcher(storage=storage)
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    print('__main__')
    asyncio.run(main())
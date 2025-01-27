from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import csv
import requests
import time
from datetime import datetime, timedelta
from collections import defaultdict

# Токен бота
API_TOKEN = '1123'
vkToken = '234'
vkApi = '5.131'
arrWord = ['а','о','1',' ','у', 'и']
#arrWord = ['й','ц','у','к','е','н','г','ш','щ','з','х','ф','в','а','п','р','о','л','д','ж','э','я','ч','с','м','и','т','б','.',',','q',' ','q','w','e','r','t','y','u','i','o','p','a','s','d','f','g','h','j','k','l','z','x','c','v','b','n','m','1','2','3','4','5','6','7','8','9','0']
file_path = 'events.csv'

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

day_of_week_rus = {
    'Monday': 'Понедельник',
    'Tuesday': 'Вторник',
    'Wednesday': 'Среда',
    'Thursday': 'Четверг',
    'Friday': 'Пятница',
    'Saturday': 'Суббота',
    'Sunday': 'Воскресенье'
}

# Список городов
# cities = ['Москва', 'Новосибирск', 'Санкт-Петербург', 'Омск', 'Томск', 'Екатеринбург', 'Барнаул', 'Искитим', 'Кемерово', 'Новокузнецк']

#arrWord = ['й','ц','у','к','е','н','г','ш','щ','з','х','ф','в','а','п','р','о','л','д','ж','э','я','ч','с','м','и','т','б','.',',','q',' ','q','w','e','r','t','y','u','i','o','p','a','s','d','f','g','h','j','k','l','z','x','c','v','b','n','m','1','2','3','4','5','6','7','8','9','0']



# https://api.vk.com/method/database.getCities?v=5.131&country_id=1&count=1&&access_token=vk1.a.1TEjyITsvJ_4YNAXkFSfk36gYNL0DiPVaoKv5txYoGYaR2-V0bQu8Kk5ElDDSeCjSycFIs44gZSVYvdR40EGlnWhXjO1FEB1sf9uLvs9Koue3ts3lXKwJVzPMegcS30yoh3802cXlQcRe2jovWqgKukh6jYNb1EjZcQvf3X2qN5V1nRDtEcJ0vhhDzzE7rj7VmXbZLqBW_Wb4X-NL2z3Lg
# Функция для получения событий
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
            print(58)
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
        print(f"Запрос URL: {url}")  # Выводим URL в консоль
        response = requests.get(url)
        data = response.json()
        if 'response' in data:
            group_info.extend(data['response'])
        time.sleep(1)  # Задержка
    return group_info

def get_info_from_groups(groups, week):
    events_by_date = defaultdict(list)
    unique_events = set()  # Множество для хранения уникальных идентификаторов событий

    # Сбор событий по датам
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

                # Создаем уникальный идентификатор события
                event_id = (screen_name_link, name)  # Используем screen_name_link и name для уникальности

                if week == 1:
                    start_of_week = today - timedelta(days=today.weekday())  # Понедельник
                    end_of_week = start_of_week + timedelta(days=6)  # Воскресенье
                    # Проверяем, попадает ли событие на текущую неделю
                    if start_of_week <= start_date_dt <= end_of_week and event_id not in unique_events:
                        unique_events.add(event_id)  # Добавляем идентификатор в множество
                        events_by_date[start_date_formatted].append((day_of_week, name, screen_name_link))
                else:
                    if event_id not in unique_events:
                        unique_events.add(event_id)  # Добавляем идентификатор в множество
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
        print(f"Запрос URL: {urlAll}")  # Выводим URL в консоль
        response = requests.get(urlAll)
        data = response.json()
        if 'response' in data and 'items' in data['response']:
            for event in data['response']['items']:
                arrLinkVkAll.append(event['screen_name'])
        time.sleep(0.5)  # Задержка
    return arrLinkVkAll

def extract_unique_cities(file_path):
    cities = set()  # Используем множество для хранения уникальных городов
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=';')  # Читаем CSV с разделителем ';'
        for row in reader:
            city = row['city'].strip()  # Убираем лишние пробелы
            if city:  # Проверяем, что город не пустой
                cities.add(city)  # Добавляем город в множество
    return list(cities)  # Преобразуем множество в список

cities = extract_unique_cities('events.csv')

# Главное меню
def main_menu(arr = 0):
    if arr == 0:
        keyboard = InlineKeyboardMarkup(row_width=4)
        keyboard.add(
            InlineKeyboardButton("Домой", callback_data="start"),
            InlineKeyboardButton("Поиск города", callback_data="get_city"),
            InlineKeyboardButton("Города СФО", callback_data="get_cities_from_db"),
            InlineKeyboardButton("Помощь", callback_data="help")
        )
    else:
        keyboard = [InlineKeyboardButton("Домой", callback_data="start"),
                    InlineKeyboardButton("Поиск города", callback_data="get_city"),
                    InlineKeyboardButton("Города СФО", callback_data="get_cities_from_db"),
                    InlineKeyboardButton("Помощь", callback_data="help")]
    return keyboard
    
def cities_menu(page=0, per_page=4):
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

# Меню событий для города
def events_menu(city):
    keyboard = [
        InlineKeyboardButton(f"Тусы недели города {city}", callback_data=f"get_events_week_{city}"),
        InlineKeyboardButton(f"Все тусы города {city}", callback_data=f"get_events_all_{city}")
    ]
    return keyboard

# Команда /start
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.answer("Добро пожаловать! Выберите опцию:", reply_markup=main_menu())

# Команда /help
@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    await message.answer("Тут будет хэлпник", reply_markup=main_menu())

# Команда /get_city
@dp.message_handler(commands=['get_city'])
async def get_city_command(message: types.Message):
    await message.answer("Введите название города", reply_markup=main_menu())

# Команда /get_cities_from_db
@dp.message_handler(commands=['get_cities_from_db'])
async def get_cities_from_db_command(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[cities_menu(), main_menu(1)])
    await message.answer("Выберите город из списка:", reply_markup=keyboard)

# Обработка нажатий на кнопки
@dp.callback_query_handler(lambda c: True)
async def process_callback(callback_query: types.CallbackQuery):
    print(236)
    data = callback_query.data

    # Домой
    if data == "start":
        await callback_query.message.edit_text("Добро пожаловать! Выберите опцию:", reply_markup=main_menu())

    # Поиск города
    elif data == "get_city":
        await callback_query.message.edit_text("Введите название города", reply_markup=main_menu())

    # Города СФО
    elif data == "get_cities_from_db":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[cities_menu(), main_menu(1)])
        await callback_query.message.edit_text("Выберите город из списка:", reply_markup=keyboard)

    # Помощь
    elif data == "help":
        await callback_query.message.edit_text("Тут будет хэлпник", reply_markup=main_menu())

    # Пагинация городов
    elif data.startswith("page_"):
        page = int(data.split("_")[1])
        keyboard = InlineKeyboardMarkup(inline_keyboard=[cities_menu(page=page), main_menu(1)])
        await callback_query.message.edit_text("Выберите город из списка:", reply_markup=keyboard) #cities_menu(page=page)

    # Выбор города
    elif data.startswith("city_"):
        city = data.split("_")[1]
        if city in cities:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[events_menu(city),main_menu(1)])
            await callback_query.message.edit_text(f"Тусы {city} уже есть. Выберите опцию:", reply_markup=keyboard)
        else:
            await callback_query.message.edit_text("Введите другой город", reply_markup=main_menu())

    # Тусы недели города
    elif data.startswith("get_events_week_"):
        print('get_events_week_')
        city = data.split("_")[3]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[events_menu(city), main_menu(1)])
        if city in cities:
            print(266)
            grouped_events = get_events_from_csv(city, 1)
            if (len(grouped_events) == 1):
                await callback_query.message.edit_text(f"Это тусы недели для города {city} \n {grouped_events[0]}", reply_markup=keyboard, parse_mode="Markdown",disable_web_page_preview=True)
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
                await bot.send_message(callback_query.from_user.id, f"Выше тусы недели для города {city}", reply_markup=keyboard, parse_mode="Markdown",disable_web_page_preview=True)
        else:
            print(288)
            city = get_city(city)
            city_id = city['id']
            city_title = city['title']
            await callback_query.message.edit_text(f"Ожидайте", disable_web_page_preview=True)
            events = get_events(city_id)
            groups = get_group_info(events)
            events_from_groups = get_info_from_groups(groups, 1)
            if (len(events_from_groups) == 1):
                await callback_query.message.edit_text(f"Это тусы недели для города {city_title} \n {events_from_groups[0]}", reply_markup=keyboard, parse_mode="Markdown",disable_web_page_preview=True)
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
                await bot.send_message(callback_query.from_user.id, f"Это тусы недели для города {city_title}", reply_markup=keyboard, parse_mode="Markdown",disable_web_page_preview=True)
    # Все тусы города
    elif data.startswith("get_events_all_"):
        city = data.split("_")[3]
        print(289)
        grouped_events = get_events_from_csv(city, 0)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[events_menu(city), main_menu(1)])
        if city in cities:
            print(305)
            if (len(grouped_events) == 1):
                await callback_query.message.edit_text(f"Это все тусы для города {city} \n {grouped_events[0]}", reply_markup=keyboard, parse_mode="Markdown",disable_web_page_preview=True)
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
                await bot.send_message(callback_query.from_user.id, f"Выше все тусы для города {city}", reply_markup=keyboard, parse_mode="Markdown",disable_web_page_preview=True)
        else:
            print(320)
            city = get_city(city)
            city_id = city['id']
            city_title = city['title']
            events = get_events(city_id)
            groups = get_group_info(events)
            events_from_groups = get_info_from_groups(groups, 0)
            if (len(events_from_groups) == 1):
                await callback_query.message.edit_text(f"Это все тусы для города {city_title} \n {events_from_groups[0]}", reply_markup=keyboard, parse_mode="Markdown",disable_web_page_preview=True)
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
                await bot.send_message(callback_query.from_user.id, f"Выше все тусы для города {city_title}", reply_markup=keyboard, parse_mode="Markdown",disable_web_page_preview=True)

@dp.message_handler(lambda message: True)
async def get_text(message: types.Message):
    print("get_text")
    if message.text in cities:  # Проверяем, есть ли город в массиве
        keyboard = InlineKeyboardMarkup(inline_keyboard=[events_menu(message.text),main_menu(1)])
        await message.answer(f"Тусы {message.text} уже есть. Выберите опцию:", reply_markup=keyboard)
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
            await message.answer("Не нашли такого города, введите другой", reply_markup=main_menu())
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[events_menu(city_title),main_menu(1)])
            await message.answer(f"Город {city_title} найден. Выберите опцию:", reply_markup=keyboard)

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

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
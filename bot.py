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
API_TOKEN = '123'

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Список городов
# cities = ['Москва', 'Новосибирск', 'Санкт-Петербург', 'Омск', 'Томск', 'Екатеринбург', 'Барнаул', 'Искитим', 'Кемерово', 'Новокузнецк']

#arrWord = ['й','ц','у','к','е','н','г','ш','щ','з','х','ф','в','а','п','р','о','л','д','ж','э','я','ч','с','м','и','т','б','.',',','q',' ','q','w','e','r','t','y','u','i','o','p','a','s','d','f','g','h','j','k','l','z','x','c','v','b','n','m','1','2','3','4','5','6','7','8','9','0']


vkToken = '234'  
vkApi = '5.131'
arrWord = ['а','о','1']

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
            return data['response']['items'][0]['id']
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
    
    # Сбор событий по датам
    for event in groups:
        if week == 1:
            try:
                start_date = event.get('start_date')
                today = datetime.now()
                start_of_week = today - timedelta(days=today.weekday())  # Понедельник
                end_of_week = start_of_week + timedelta(days=6)  # Воскресенье
                if start_date and start_date > int(datetime.now().timestamp()):
                    start_date_dt = datetime.fromtimestamp(start_date)
                    
                    # Проверяем, попадает ли событие на текущую неделю
                    if start_of_week <= start_date_dt <= end_of_week:
                        start_date_formatted = start_date_dt.strftime('%d.%m.%Y')
                        day_of_week = start_date_dt.strftime('%A')
                        screen_name_link = event.get('screen_name')
                        name = event.get('name', '').replace('[', ' ').replace(']', ' ').replace('{', ' ').replace('}', ' ').replace('|', ' ')
                        
                        events_by_date[start_date_formatted].append((day_of_week, name, screen_name_link))
            except Exception as e:
                print(f"Ошибка при обработке события: {e}")
        else:
            try:
                start_date = event.get('start_date')
                if start_date and start_date > int(datetime.now().timestamp()):
                    start_date_formatted = datetime.fromtimestamp(start_date).strftime('%d.%m.%Y')
                    day_of_week = datetime.fromtimestamp(start_date).strftime('%A')
                    screen_name_link = event.get('screen_name')
                    name = event.get('name', '').replace('[', ' ').replace(']', ' ').replace('{', ' ').replace('}', ' ').replace('|', ' ')
                    
                    events_by_date[start_date_formatted].append((day_of_week, name, screen_name_link))
            except Exception as e:
                print(f"Ошибка при обработке события: {e}")

    # Составляем финальное сообщение
    messages = ''
    message = ''
    max_length = 4096  # Максимальная длина сообщения в Telegram
    
    day_of_week_rus = {
        'Monday': 'Понедельник',
        'Tuesday': 'Вторник',
        'Wednesday': 'Среда',
        'Thursday': 'Четверг',
        'Friday': 'Пятница',
        'Saturday': 'Суббота',
        'Sunday': 'Воскресенье'
    }
    
    for date in sorted(events_by_date.keys(), key=lambda x: datetime.strptime(x, '%d.%m.%Y')):
        day_of_week = day_of_week_rus[events_by_date[date][0][0]]
        
        # Добавляем дату и события в сообщение
        message += f"\n{day_of_week} {date} \n"
        for event in events_by_date[date]:
            message += f"[{event[1]}](https://vk.com/{event[2]})\n"
        
        # Проверка длины сообщения и деление на части если необходимо
        if len(message) > max_length:
            messages += message[:-1]  # Добавляем последнюю часть сообщения без последнего переноса строки
            message = ''  # Очищаем сообщение
    
    # Добавляем последнюю часть сообщения
    if message:
        messages += message

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
def main_menu():
    keyboard = InlineKeyboardMarkup(row_width=4)
    keyboard.add(
        InlineKeyboardButton("Домой", callback_data="start"),
        InlineKeyboardButton("Поиск города", callback_data="get_city"),
        InlineKeyboardButton("Города СФО", callback_data="get_cities_from_db"),
        InlineKeyboardButton("Помощь", callback_data="help")
    )
    return keyboard
    
def cities_menu(page=0, per_page=4):
    keyboard = InlineKeyboardMarkup(row_width=4)
    start = page * per_page
    end = start + per_page

    # Добавляем города на текущей странице
    for city in cities[start:end]:
        keyboard.insert(InlineKeyboardButton(city, callback_data=f"city_{city}"))

    # Проверяем, есть ли предыдущая страница
    if page > 0:
        keyboard.insert(InlineKeyboardButton("<<", callback_data=f"page_{page - 1}"))

    # Проверяем, есть ли следующая страница
    if end < len(cities):
        keyboard.insert(InlineKeyboardButton(">>", callback_data=f"page_{page + 1}"))

    # Если это последняя страница и остались города
    if end >= len(cities) and start < len(cities):
        remaining_cities = cities[end:]
        for city in remaining_cities:
            keyboard.insert(InlineKeyboardButton(city, callback_data=f"city_{city}"))

    return keyboard

# Меню событий для города
def events_menu(city):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(f"Тусы недели города {city}", callback_data=f"get_events_week_{city}"),
        InlineKeyboardButton(f"Все тусы города {city}", callback_data=f"get_events_all_{city}")
    )
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
    await message.answer("Выберите город из списка:", reply_markup=cities_menu())

# Обработка нажатий на кнопки
@dp.callback_query_handler(lambda c: True)
async def process_callback(callback_query: types.CallbackQuery):
    data = callback_query.data

    # Домой
    if data == "start":
        await callback_query.message.edit_text("Добро пожаловать! Выберите опцию:", reply_markup=main_menu())

    # Поиск города
    elif data == "get_city":
        await callback_query.message.edit_text("Введите название города", reply_markup=main_menu())

    # Города СФО
    elif data == "get_cities_from_db":
        await callback_query.message.edit_text("Выберите город из списка:", reply_markup=cities_menu())

    # Помощь
    elif data == "help":
        await callback_query.message.edit_text("Тут будет хэлпник", reply_markup=main_menu())

    # Пагинация городов
    elif data.startswith("page_"):
        page = int(data.split("_")[1])
        await callback_query.message.edit_text("Выберите город из списка:", reply_markup=cities_menu(page=page))

    # Выбор города
    elif data.startswith("city_"):
        city = data.split("_")[1]
        if city in cities:
            await callback_query.message.edit_text(f"Тусы {city} уже есть. Выберите опцию:", reply_markup=events_menu(city))
        else:
            await callback_query.message.edit_text("Введите другой город", reply_markup=main_menu())

    # Тусы недели города
    elif data.startswith("get_events_week_"):
        city = data.split("_")[3]
        if city in cities:
            await callback_query.message.edit_text(f"Это тусы недели для города {city}", reply_markup=main_menu())
        else:
            city_id = get_city(city)
            events = get_events(city_id)
            groups = get_group_info(events)
            events_from_groups = get_info_from_groups(groups, 1)
            print(events_from_groups)
            await callback_query.message.edit_text(f"Это тусы недели для города {city} \n {events_from_groups}", reply_markup=main_menu(), parse_mode="Markdown",)
    # Все тусы города
    elif data.startswith("get_events_all_"):
        city = data.split("_")[3]
        #await callback_query.message.edit_text(f"Это все тусы для города {city}", reply_markup=main_menu())
        if city in cities:
            await callback_query.message.edit_text(f"Это все тусы для города {city}", reply_markup=main_menu())
        else:
            city_id = get_city(city)
            events = get_events(city_id)
            groups = get_group_info(events)
            events_from_groups = get_info_from_groups(groups, 0)
            print(events_from_groups)
            await callback_query.message.edit_text(f"Это все тусы для города {city} \n {events_from_groups}", reply_markup=main_menu(), parse_mode="Markdown",)

@dp.message_handler(lambda message: True)
async def get_text(message: types.Message):
    print("get_text")
    if message.text in cities:  # Проверяем, есть ли город в массиве
        #await message.answer("вы ввели "+message.text, reply_markup=main_menu())
        await message.answer(f"Тусы {message.text} уже есть. Выберите опцию:", reply_markup=events_menu(message.text))
    else:
        # ищем город в ВК. Если не нашли, сообщение
        city_id = get_city(message.text)
        if city_id == '':
            await message.answer("Не нашли такого города, введите другой", reply_markup=main_menu())
        else:
            await message.answer(f"Город {message.text} найден. Выберите опцию:", reply_markup=events_menu(message.text))

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
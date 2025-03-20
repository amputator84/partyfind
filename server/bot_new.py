# aiogram 2.25.1
# python 3.11.0
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import csv
import datetime
from datetime import timedelta
import urllib.parse
import requests

import time

API_TOKEN = '123'
# токен для поста
vkToken = '321'
# токен для сбора тус по городам из https://oauth.vk.com/blank.html...
vkTokenAll = '333'
vkApi = '5.131'
arrWord = [' ','1']
#arrWord = ['й','ц','у','к','е','н','г','ш','щ','з','х','ф','в','а','п','р','о','л','д','ж','э','я','ч','с','м','и','т','б','.',',','q',' ','q','w','e','r','t','y','u','i','o','p','a','s','d','f','g','h','j','k','l','z','x','c','v','b','n','m','1','2','3','4','5','6','7','8','9','0']
cities = ['Абакан','Искитим','Новосибирск','Барнаул','Томск','Омск','Кемерово','Новокузнецк','Красноярск','Междуреченск','Новоалтайск','Горно-Алтайск','Шерегеш','Бердск','Москва','Санкт-Петербург','Екатеринбург']
owner_id = '111'
client_id = '222'

day_of_week_rus = {
    'Monday': 'Понедельник',
    'Tuesday': 'Вторник',
    'Wednesday': 'Среда',
    'Thursday': 'Четверг',
    'Friday': 'Пятница',
    'Saturday': 'Суббота',
    'Sunday': 'Воскресенье'
}

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

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

# Меню событий для города
def events_menu(city):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(f"Тусы недели города {city}", callback_data=f"get_events_week_{city}"),
        InlineKeyboardButton(f"Все тусы города {city}", callback_data=f"get_events_all_{city}")
    )
    return keyboard

def extract_unique_cities(file_path):
    cities = set()  # Используем множество для хранения уникальных городов
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=';')  # Читаем CSV с разделителем ';'
        for row in reader:
            city = row['city'].strip()  # Убираем лишние пробелы
            if city:  # Проверяем, что город не пустой
                cities.add(city)  # Добавляем город в множество
    return list(cities)  # Преобразуем множество в список

citiesArr = extract_unique_cities('events.csv')

def get_city_ids(cities):
    city_ids = []
    for city in cities:
        response = requests.get(
            'https://api.vk.com/method/database.getCities',
            params={
                'access_token': vkTokenAll,
                'v': vkApi,
                'country_id': 1,
                'q': city,
                'count': 1
            }
        )
        try:
            data = response.json()
            #print(response.json())
            if 'response' in data and 'items' in data['response'] and len(data['response']['items']) > 0:
                city_ids.append(data['response']['items'][0]['id'])
            else:
                print(f"Город '{city}' не найден.")
                return False
        except Exception as e:
            print(f"Ошибка {e}")
        time.sleep(0.5)
    return city_ids

def get_events(city_id):
    arrLinkVkAll = []
    for word in arrWord:
        urlAll = f"https://api.vk.com/method/groups.search/?q={word}&type=event&city_id={city_id}&future=1&offset=0&count=999&access_token={vkTokenAll}&v={vkApi}"
        print(f"Запрос URL: {urlAll}")
        response = requests.get(urlAll)
        data = response.json()
        if 'response' in data and 'items' in data['response']:
            for event in data['response']['items']:
                arrLinkVkAll.append(event['screen_name'])
        time.sleep(0.5)
    return arrLinkVkAll

def get_group_info(group_ids):
    group_info = []
    for i in range(0, len(group_ids), 500):
        groupIds = ','.join(group_ids[i:i + 500])
        url = f"https://api.vk.com/method/groups.getById/?group_ids={groupIds}&fields=start_date,finish_date,description,city&access_token={vkTokenAll}&v={vkApi}"
        print(f"Запрос URL: {url}") 
        response = requests.get(url)
        data = response.json()
        if 'response' in data:
            group_info.extend(data['response'])
        time.sleep(1)
    return group_info

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
        event['start_date'] = datetime.datetime.strptime(event['start_date'], '%d.%m.%Y')

    if week == 1:
        today = datetime.datetime.utcnow()
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
    message_parts = []
    for weekday, events in grouped_events.items():
        message_parts.append(f"{day_of_week_rus[weekday]} {events[0]['start_date'].strftime('%d.%m.%Y')}")
        for event in events:
            #message_parts.append(f"{event['name']} ({event['screen_name_link']})")
            message_parts.append(f"[{event['name']}](https://vk.com/{event['screen_name_link']})")
            # f"[{event[1]}](https://vk.com/{event[2]})\n"
        message_parts.append("")  # Добавляем пустую строку для разделения

    #return "\n".join(message_parts).strip()
    formatted_message = "\n".join(message_parts).strip()
    messages = ''
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
                #await message.answer(current_part.strip(), parse_mode="Markdown", disable_web_page_preview=True)
                messages += current_part.strip()
                current_part = line + '\n'  # Начинаем новую часть с текущей строки
        
        # Отправляем оставшуюся часть
        if current_part:
            #await message.answer(current_part.strip(), parse_mode="Markdown", disable_web_page_preview=True)
            messages += current_part.strip()
    else:
        #await message.answer(formatted_message, parse_mode="Markdown", disable_web_page_preview=True)
        messages += formatted_message
    return messages

def get_events_from_csv(city, week):
    events = read_csv('events.csv')
    grouped_events = group_events_by_weekday(events, city, week)
    formatted_message = format_message(grouped_events)
    return formatted_message

# Команда /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Нажми на кнопку ниже.", reply_markup=await get_keyboard())

# Функция для создания клавиатуры
async def get_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = types.KeyboardButton("getPost")
    keyboard.add(button)
    button = types.KeyboardButton("getAll")
    keyboard.add(button)
    return keyboard

@dp.message_handler(lambda message: message.text == "getPost")
@dp.message_handler(commands=['getPost'])
async def handle_button_click(message: types.Message):
    # Здесь вы можете вызвать ваш скрипт getPost
    # Получаем текущую дату
    current_date = datetime.datetime.utcnow()
    current_weekday = current_date.strftime('%A')
    current_date_str = current_date.strftime('%d.%m.%Y')
    today_date = current_date.strftime('%d.%m.%Y')  # Получаем дату в формате ДД.ММ.ГГГГ

    # Словарь для хранения событий по дате
    events_by_date = {}

    # Открываем файл events.csv
    with open('events.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=';')
        
        # Проходим по строкам файла
        for row in reader:
            # Проверяем, совпадает ли дата события с текущей
            if row['start_date'] == current_date_str and row['city'] not in ['Москва', 'Санкт-Петербург', 'Екатеринбург']:
                city = row['city']
                screen_name_link = row['screen_name_link']
                name = row['name']
                
                # Формируем запись события
                event_entry = f"[{screen_name_link}|{name}]"
                
                # Добавляем событие в словарь
                if current_date_str not in events_by_date:
                    events_by_date[current_date_str] = {}
                if city not in events_by_date[current_date_str]:
                    events_by_date[current_date_str][city] = []
                events_by_date[current_date_str][city].append(event_entry)

    # Выводим результаты
    for date, cities in events_by_date.items():
        weekday_russian = {
            'Monday': 'Понедельник',
            'Tuesday': 'Вторник',
            'Wednesday': 'Среда',
            'Thursday': 'Четверг',
            'Friday': 'Пятница',
            'Saturday': 'Суббота',
            'Sunday': 'Воскресенье'
        }
        
        # Формируем текст для публикации
        txtUrl = ""
        for city, names in events_by_date.items():
            txtUrl += f"{weekday_russian[current_weekday]} {date}\n"
        
        for city, events in cities.items():
            txtUrl += f"\n{city}\n"  # Перенос строки перед названием города
            for event in events:
                txtUrl += f"{event}\n"
        
        txtUrl += '\n'
        txtUrl += "#тусынавыхи Остальное goo.gl/Df6FBQ"
        print(txtUrl)
        await message.reply(txtUrl)
    # Кодируем текст для URL
    encoded_txtUrl = urllib.parse.quote(txtUrl)

    # Задаем параметры для запроса к API ВКонтакте
    tomorrow = int((current_date + datetime.timedelta(days=1)).timestamp())
    url = f'https://api.vk.com/method/wall.post?v=5.107&owner_id=-{owner_id}&access_token={vkToken}&from_group=1&message={encoded_txtUrl}&publish_date={tomorrow}'

    # Отправляем запрос
    response = requests.get(url)
    print(response.json())
    await message.reply('Пост добавлен')


@dp.message_handler(lambda message: message.text == "getAll")
@dp.message_handler(commands=['getAll'])
async def handle_button_click(message: types.Message):
    endUrls = []
    unique_events = set()
    if get_city_ids(cities) == False:
        await message.reply('Обнови https://oauth.vk.com/authorize?client_id={client_id}&scope=groups&redirect_uri=http%3A%2F%2Foauth.vk.com%2Fblank.html&display=page&response_type=token')
    else:
        await message.reply('Пошла возня')
        city_ids = get_city_ids(cities)
        for city_id in city_ids:
            print(f"Обработка города с ID: {city_id}")
            arrLinkVkAll = get_events(city_id)
            
            group_info = get_group_info(arrLinkVkAll)
            for event in group_info:
                try:
                    start_date = event.get('start_date')
                    finish_date = event.get('finish_date', '')
                    description = event.get('description', '')
                    city = event.get('city', {})

                    if start_date and start_date > int(datetime.datetime.now().timestamp()):  # Используем datetime.datetime
                        start_date_formatted = datetime.datetime.fromtimestamp(start_date).strftime('%d.%m.%Y')  # Используем datetime.datetime
                        screen_name = f'=HYPERLINK("https://vk.com/{event["screen_name"]}";"{event["screen_name"]}")'
                        screen_name_link = event.get('screen_name')
                        name = event.get('name', '').replace('[', ' ').replace(']', ' ').replace('{', ' ').replace('}', ' ').replace('|', ' ')
                        description = description.replace('[', ' ').replace(']', ' ').replace('{', ' ').replace('}', ' ').replace('|', ' ')

                        if city.get('title'):
                            event_tuple = (city['title'], name, screen_name, start_date_formatted, description)
                            if event_tuple not in unique_events:
                                unique_events.add(event_tuple)
                                endUrls.append({
                                    'city': city['title'],
                                    'name': name,
                                    'screen_name': screen_name,
                                    'start_date': start_date_formatted,
                                    'screen_name_link': screen_name_link,
                                    'description': description
                                })
                except Exception as e:
                    print(f"Ошибка при обработке события: {e}")
        endUrls.sort(key=lambda x: (x['city'], datetime.datetime.strptime(x['start_date'], '%d.%m.%Y')))  # Используем datetime.datetime
        with open('events.csv', 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['city', 'name', 'screen_name', 'start_date', 'screen_name_link', 'description']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            for row in endUrls:
                writer.writerow(row)
        await message.reply('Добавлено')

# Обработка нажатий на кнопки
@dp.callback_query_handler(lambda c: True)
async def process_callback(callback_query: types.CallbackQuery):
    data = callback_query.data
    if data.startswith("get_events_week_"):
        city = data.split("_")[3]
        grouped_events = get_events_from_csv(city, 1)
        #await callback_query.message.edit_text(f"Проверка города {city}")
        #await bot.send_message(callback_query.from_user.id, f"Проверка города {city} - тусы {grouped_events}")
        await callback_query.message.edit_text(f"Это все тусы для города {city} \n {grouped_events}", reply_markup=main_menu(), parse_mode="Markdown", disable_web_page_preview=True)
    elif data.startswith("get_events_all_"):
        city = data.split("_")[3]
        grouped_events = get_events_from_csv(city, 0)
        if city in cities:
            if len(grouped_events) > 4096:
                await callback_query.message.edit_text(f"Это все тусы для города {city}", reply_markup=main_menu())
                # тут вставить цикл разделения сообщений с прокидыванием bot и выводом bot.send_message
                await bot.send_message(callback_query.from_user.id, "Первое сообщение")
                await bot.send_message(callback_query.from_user.id, "Второе сообщение")
            else:
                await callback_query.message.edit_text(f"Это все тусы для города {city} \n {grouped_events}", reply_markup=main_menu())

@dp.message_handler(lambda message: True)
async def get_text(message: types.Message):
    print("get_text")
    if message.text in citiesArr:  # Проверяем, есть ли город в массиве
        await message.answer(f"Тусы города {message.text} уже есть. Выберите опцию:", reply_markup=events_menu(message.text))
    else:
        city_id = get_city_ids([message.text])
        print(city_id)
        if city_id == '' or city_id == False:
            await message.answer(f"Не нашли город {message.text}, введите другой", reply_markup=main_menu())
        else:
            await message.answer(f"Город {message.text} найден. Выберите опцию:", reply_markup=events_menu(message.text))

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
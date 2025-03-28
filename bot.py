# aiogram 2.25.1
# python 3.11.0
import config
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import csv
from datetime import datetime, timedelta
import urllib.parse
import requests
import time

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.api_token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

#config.arr_word = ['1',' ', 'а', 'о', 'е']
#config.cities = ['Барнаул','Томск','Екатеринбург']

# Главное меню
def main_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
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

# Список городов из csv
def extract_unique_cities(file_path):
    cities = set()
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=';')  # Читаем CSV с разделителем ';'
        for row in reader:
            city = row['city'].strip()
            if city:
                cities.add(city)
    return list(cities)

cities_csv = extract_unique_cities('events.csv')

# Поиск id городов в ВК. cities = ['Омск','Томск']
def get_city_ids(cities):
    print('get_city_ids')
    city_ids = []
    for city in cities:
        response = requests.get(
            'https://api.vk.com/method/database.getCities',
            params={
                'access_token': config.vk_token_all,
                'v': config.vk_api,
                'country_id': 1,
                'q': city,
                'count': 1
            }
        )
        data = response.json()
        if 'response' in data and 'items' in data['response'] and len(data['response']['items']) > 0:
            city_ids.append(data['response']['items'][0])
        else:
            print(f"Город '{city}' не найден.")
            if 'error' in data:
                print(f'Обнови https://oauth.vk.com/authorize?client_id={config.client_id}&scope=groups&redirect_uri=http%3A%2F%2Foauth.vk.com%2Fblank.html&display=page&response_type=token')
            return False
        time.sleep(0.5) # чтоб не DDOS`ить`
    return city_ids

# поиск тус в цикое по словам из word. Каждая итерация максимум по 999 тус
async def get_events(city_id, city_name, callback_query):
    arr_link_vk_all = []
    word_len = len(config.arr_word)
    i = word_len
    countdown_message = await callback_query.message.edit_text(f"Поиск тус города {city_name}. Осталось {i}", reply_markup=events_menu(city_name), parse_mode="Markdown",disable_web_page_preview=True)
    for word in config.arr_word:
        i = i - 1
        await countdown_message.edit_text(f"Поиск тус города {city_name}. Осталось {i}", reply_markup=events_menu(city_name), parse_mode="Markdown",disable_web_page_preview=True)
        url_all = f"https://api.vk.com/method/groups.search/?q={word}&type=event&city_id={city_id}&future=1&offset=0&count=999&access_token={config.vk_token_all}&v={config.vk_api}"
        response = requests.get(url_all)
        data = response.json()
        if 'response' in data and 'items' in data['response']:
            for event in data['response']['items']:
                arr_link_vk_all.append(event['screen_name'])
        time.sleep(0.5)
    return arr_link_vk_all

# поиск информации о группе по массиву id. Максимум в одной итерации 500 id
def get_group_info(group_ids):
    group_info = []
    for i in range(0, len(group_ids), 500):
        groupIds = ','.join(group_ids[i:i + 500])
        url = f"https://api.vk.com/method/groups.getById/?group_ids={groupIds}&fields=start_date,finish_date,description,city&access_token={config.vk_token_all}&v={config.vk_api}"
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

# Возвращает тусы, сгруппированные по дням недели
def group_events_by_weekday(events, city, week):
    print('group_events_by_weekday')
    print(city)
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

# Группировка по датам и дням недели, проставление ссылок, обрезка длинных сообщений
def format_message(grouped_events, week):
    message_parts = []

    if week == 1:
        for weekday, events in grouped_events.items():
            message_parts.append(f"{config.day_of_week_rus[weekday]} {events[0]['start_date'].strftime('%d.%m.%Y')}")
            for event in events:
                message_parts.append(f"[{event['name']}](https://vk.com/{event['screen_name_link']})")
            message_parts.append("")
    else:
        # Получаем минимальную и максимальную даты из событий
        all_dates = []
        for events in grouped_events.values():
            for event in events:
                all_dates.append(event['start_date'])
        
        min_date = min(all_dates)
        max_date = max(all_dates)
        current_date = min_date
        
        while current_date <= max_date:
            # Проверяем, есть ли события на текущую дату
            events_today = []
            for events in grouped_events.values():
                for event in events:
                    if event['start_date'].date() == current_date.date():
                        events_today.append(event)
            
            # Если есть события на текущую дату, добавляем их в сообщение
            if events_today:
                weekday = current_date.strftime('%A')
                message_parts.append(f"{config.day_of_week_rus[weekday]} {current_date.strftime('%d.%m.%Y')}")
                for event in events_today:
                    message_parts.append(f"[{event['name']}](https://vk.com/{event['screen_name_link']})")
                message_parts.append("")
            current_date += timedelta(days=1)
    
    formatted_message = "\n".join(message_parts).strip()
    messages = []
    
    # Ограничение одного сообщения telegram
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

# Возвращаем форматированные тусы из csv
def get_events_from_csv(city, week):
    events = read_csv('events.csv')
    grouped_events = group_events_by_weekday(events, city, week)
    formatted_message = format_message(grouped_events, week)
    return formatted_message

# Возвращаем форматированные тусы из VK
async def get_events_from_city_web(city, week, callback_query):
    end_urls = []
    unique_events = set()
    city_find = get_city_ids([city])
    city_id = city_find[0]['id']
    city_name = city_find[0]['title']
    arr_link_vk_all = await get_events(city_id, city_name, callback_query)
    group_info = get_group_info(arr_link_vk_all)
    for event in group_info:
        try:
            start_date = event.get('start_date')
            city_event = event.get('city', {})
            if start_date and start_date > int(datetime.now().timestamp()):
                start_date_formatted = datetime.fromtimestamp(start_date).strftime('%d.%m.%Y')
                screen_name_link = event.get('screen_name')
                name = event.get('name', '').replace('[', ' ').replace(']', ' ').replace('{', ' ').replace('}', ' ').replace('|', ' ')

                if city_event.get('title'):
                    event_tuple = (city_event['title'], name, start_date_formatted)
                    if event_tuple not in unique_events:
                        unique_events.add(event_tuple)
                        end_urls.append({
                            'city': city_event['title'],
                            'name': name,
                            'start_date': start_date_formatted,
                            'screen_name_link': screen_name_link
                        })
        except Exception as e:
            print(f"Ошибка при обработке события: {e}")
    end_urls.sort(key=lambda x: (x['city'], datetime.strptime(x['start_date'], '%d.%m.%Y')))
    grouped_events = group_events_by_weekday(end_urls, city_name, week)
    formatted_message = format_message(grouped_events, week)
    return formatted_message

# Отправка тус в TG с промежуточными сообщениями
async def send_messages_events(city, week, csv, callback_query):
    if csv == 1:
        events = get_events_from_csv(city, week)
    else:
        events = await get_events_from_city_web(city, week, callback_query)
    week_text = ' недели' if week == 1 else ''
    if (events[0] == ''):
        await callback_query.message.edit_text(f"Для города {city} нет тус{week_text}, попробуй выбери \"Все тусы\"", reply_markup=events_menu(city), parse_mode="Markdown",disable_web_page_preview=True)
    if (len(events) == 1 and events[0] != ''):
        await callback_query.message.edit_text(f"Это тусы{week_text} города {city} \n {events[0]}", reply_markup=events_menu(city), parse_mode="Markdown",disable_web_page_preview=True)
    else:
        i = 0
        for message in events:
            if i == 0:
                msgFor = await bot.send_message(callback_query.from_user.id, f"{city}\n\n" + message, parse_mode="Markdown",disable_web_page_preview=True)
            else:
                await bot.send_message(callback_query.from_user.id, message, parse_mode="Markdown",disable_web_page_preview=True)
            i = i + 1
        await msgFor.reply(f"Выше тусы{week_text} города {city}", reply_markup=events_menu(city), parse_mode="Markdown",disable_web_page_preview=True)

# Команда /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Нажми на кнопку ниже.", reply_markup=await get_keyboard())

# Функция для создания клавиатуры
async def get_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = types.KeyboardButton("get_post")
    keyboard.add(button)
    button = types.KeyboardButton("get_all")
    keyboard.add(button)
    return keyboard

@dp.message_handler(lambda message: message.text == "get_post")
@dp.message_handler(commands=['get_post'])
async def handle_button_click(message: types.Message):
    current_date = datetime.utcnow()
    current_weekday = current_date.strftime('%A')
    current_date_str = current_date.strftime('%d.%m.%Y')
    events_by_date = {}

    with open('events.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=';')
        
        for row in reader:
            if row['start_date'] == current_date_str and row['city'] not in ['Москва', 'Санкт-Петербург', 'Екатеринбург']:
                city = row['city']
                screen_name_link = row['screen_name_link']
                name = row['name']
                event_entry = f"[{screen_name_link}|{name}]"
                if current_date_str not in events_by_date:
                    events_by_date[current_date_str] = {}
                if city not in events_by_date[current_date_str]:
                    events_by_date[current_date_str][city] = []
                events_by_date[current_date_str][city].append(event_entry)

    for date, cities in events_by_date.items():
        txt_url = ""
        for city in events_by_date.items():
            txt_url += f"{config.day_of_week_rus[current_weekday]} {date}\n"
        
        for city, events in cities.items():
            txt_url += f"\n{city}\n"  # Перенос строки перед названием города
            for event in events:
                txt_url += f"{event}\n"
        
        txt_url += '\n'
        txt_url += "#тусынавыхи Остальное goo.gl/Df6FBQ"
    encoded_txt_url = urllib.parse.quote(txt_url)
    current_date2 = datetime.now()
    tomorrow = current_date2 + timedelta(days=1)

    # Преобразуем завтрашнюю дату в миллисекунды
    tomorrow_milliseconds = int(tomorrow.timestamp())
    url = f'https://api.vk.com/method/wall.post?v=5.107&owner_id=-{config.owner_id}&access_token={config.vk_token}&from_group=1&message={encoded_txt_url}&publish_date={tomorrow_milliseconds}'

    response = requests.get(url)
    data = response.json()
    await message.reply(txt_url)
    if 'error' in data:
        await message.reply(data['error']['error_msg'],disable_web_page_preview=True)
    else:
        await message.reply('Пост добавлен',disable_web_page_preview=True)


@dp.message_handler(lambda message: message.text == "get_all")
@dp.message_handler(commands=['get_all'])
async def f_get_all(message: types.Message):
    end_urls = []
    unique_events = set()
    if get_city_ids(config.cities) == False:
        await message.reply(f'Обнови https://oauth.vk.com/authorize?client_id={config.client_id}&scope=groups&redirect_uri=http%3A%2F%2Foauth.vk.com%2Fblank.html&display=page&response_type=token')
    else:
        city_ids = get_city_ids(config.cities)
        #city_find = get_city_ids([city])[0] # ищем по одному элементу массива
        #city_id = city_find['id']
        #city_name = city_find['title']
        for city_id in city_ids:
            print(f"Обработка города с ID: {city_id}")
            arr_link_vk_all = get_events(city_id, 'Доделаю', message) # TODO
            group_info = get_group_info(arr_link_vk_all)
            for event in group_info:
                try:
                    start_date = event.get('start_date')
                    description = event.get('description', '')
                    city = event.get('city', {})
                    if start_date and start_date > int(datetime.now().timestamp()):
                        start_date_formatted = datetime.fromtimestamp(start_date).strftime('%d.%m.%Y')
                        screen_name = f'=HYPERLINK("https://vk.com/{event["screen_name"]}";"{event["screen_name"]}")'
                        screen_name_link = event.get('screen_name')
                        name = event.get('name', '').replace('[', ' ').replace(']', ' ').replace('{', ' ').replace('}', ' ').replace('|', ' ')
                        description = description.replace('[', ' ').replace(']', ' ').replace('{', ' ').replace('}', ' ').replace('|', ' ')
                        if city.get('title'):
                            event_tuple = (city['title'], name, screen_name, start_date_formatted, description)
                            if event_tuple not in unique_events:
                                unique_events.add(event_tuple)
                                end_urls.append({
                                    'city': city['title'],
                                    'name': name,
                                    'screen_name': screen_name,
                                    'start_date': start_date_formatted,
                                    'screen_name_link': screen_name_link,
                                    'description': description
                                })
                except Exception as e:
                    print(f"Ошибка при обработке события: {e}")
        end_urls.sort(key=lambda x: (x['city'], datetime.strptime(x['start_date'], '%d.%m.%Y')))
        with open('events.csv', 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['city', 'name', 'screen_name', 'start_date', 'screen_name_link', 'description']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            for row in end_urls:
                writer.writerow(row)
        await message.reply('Добавлено')

# Обработка нажатий на кнопки
@dp.callback_query_handler(lambda c: True)
async def process_callback(callback_query: types.CallbackQuery):
    print('process_callback')
    data = callback_query.data
    if data.startswith("get_events_week_"):
        city = data.split("_")[3]
        if city in config.cities:
            await send_messages_events(city, 1, 1, callback_query)
        else:
            await send_messages_events(city, 1, 0, callback_query)
    elif data.startswith("get_events_all_"):
        city = data.split("_")[3]
        if city in config.cities:
            await send_messages_events(city, 0, 1, callback_query)
        else:
            await send_messages_events(city, 0, 0, callback_query)

@dp.message_handler(lambda message: True)
async def get_text(message: types.Message):
    print("get_text")
    if message.text in cities_csv:  # Проверяем, есть ли город в csv
        await message.answer(f"Тусы города {message.text} у меня уже есть. Выберите опцию:", reply_markup=events_menu(message.text))
    else:
        city_find = get_city_ids([message.text])
        if city_find == False:
            await message.answer(f"Не нашли город {message.text}, введите другой", reply_markup=main_menu())
        else:
            city_name = city_find[0]['title']
            await message.answer(f"Город {city_name} найден. Выберите опцию:", reply_markup=events_menu(city_name))

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
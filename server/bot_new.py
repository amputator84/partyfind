import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
import csv
import datetime
import urllib.parse
import requests

import time

API_TOKEN = '123'
# токен для поста
vkToken = '123'
# токен для сбора тус по городам из https://oauth.vk.com/blank.html...
vkTokenAll = '123'
vkApi = '5.131'
arrWord = ['й','ц','у','к','е','н','г','ш','щ','з','х','ф','в','а','п','р','о','л','д','ж','э','я','ч','с','м','и','т','б','.',',','q',' ','q','w','e','r','t','y','u','i','o','p','a','s','d','f','g','h','j','k','l','z','x','c','v','b','n','m','1','2','3','4','5','6','7','8','9','0']
cities = ['Абакан','Искитим','Новосибирск','Барнаул','Томск','Омск','Кемерово','Новокузнецк','Красноярск','Междуреченск','Новоалтайск','Горно-Алтайск','Шерегеш','Бердск','Москва','Санкт-Петербург','Екатеринбург']
owner_id = '111'
client_id = '222'

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

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

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
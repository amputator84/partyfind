import vk_api  # 11.9.9
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import logging
import requests
import time
import asyncio
import csv
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
class Config:
    vk_bot_token = '123'
    vk_bot_token2 = '234'
    vk_api = '5.131'
    city_id = 99
    vk_bot_token = '123'
    vk_bot_token2 = '123'
    day_of_week_rus = {
        'Monday': 'Понедельник',
        'Tuesday': 'Вторник',
        'Wednesday': 'Среда',
        'Thursday': 'Четверг',
        'Friday': 'Пятница',
        'Saturday': 'Суббота',
        'Sunday': 'Воскресенье'
    }

config = Config()


def auth():
    vk_session = vk_api.VkApi(token=config.vk_bot_token)
    return vk_session

def extract_unique_cities(file_path):
    cities = set()
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=';')
        for row in reader:
            city = row['city'].strip()
            if city:
                cities.add(city)
    return list(cities)

cities_csv = extract_unique_cities('events.csv')

def read_csv(file_path):
    events = []
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=';')
        for row in reader:
            events.append(row)
    return events

def group_events_by_weekday(events, city, week):
    logging.info('group_events_by_weekday')
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

def format_message2(grouped_events, week):
    message_parts = []

    if week == 1:
        for weekday, events in grouped_events.items():
            message_parts.append(f"{config.day_of_week_rus[weekday]} {events[0]['start_date'].strftime('%d.%m.%Y')}")
            for event in events:
                message_parts.append(f"[{event['screen_name_link']}|{event['name']}]")
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
                    message_parts.append(f"[{event['screen_name_link']}|{event['name']}]")
                message_parts.append("")
            current_date += timedelta(days=1)
    
    formatted_message = "\n".join(message_parts).strip()
    logging.info(132)
    logging.info(len(formatted_message))
    messages = []
    
    # Ограничение одного сообщения telegram и VK
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
    logging.info(150)
    logging.info(len(messages))
    return messages

def format_message(grouped_events, week):
    message_parts = []

    if week == 1:
        for weekday, events in grouped_events.items():
            message_parts.append(f"{config.day_of_week_rus[weekday]} {events[0]['start_date'].strftime('%d.%m.%Y')}")
            for event in events:
                message_parts.append(f"[{event['screen_name_link']}|{event['name']}]")
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
                    message_parts.append(f"[{event['screen_name_link']}|{event['name']}]")
                message_parts.append("")
            current_date += timedelta(days=1)
    
    formatted_message = "\n".join(message_parts).strip()
    logging.info(132)
    logging.info(len(formatted_message))
    messages = []
    
    # Ограничение одного сообщения telegram и VK
    if len(formatted_message) > 4096:
        message_parts = formatted_message.split('\n')
        current_part = ""
        for line in message_parts:
            if len(current_part) + len(line) + 1 <= 4096:
                current_part += line + '\n'
            else:
                messages.append(current_part.strip())
                current_part = line + '\n'
        
        # Добавляем последнюю часть сообщения
        if current_part:
            messages.append(current_part.strip())
    else:
        messages.append(formatted_message)
    
    logging.info(150)
    logging.info(len(messages))
    return messages


def get_city_ids(cities):
    logging.info('get_city_ids')
    city_ids = []
    for city in cities:
        response = requests.get(
            'https://api.vk.com/method/database.getCities',
            params={
                'access_token': config.vk_bot_token2,
                'v': '5.131',
                'country_id': 1,
                'q': city,
                'count': 1
            }
        )
        data = response.json()
        if 'response' in data and 'items' in data['response'] and len(data['response']['items']) > 0:
            city_ids.append(data['response']['items'][0])
        time.sleep(0.5)  # To avoid hitting the rate limit
    return city_ids

def get_events(city_id):
    logging.info('get_events')
    arr_link_vk_all = []
    url_all = f"https://api.vk.com/method/groups.search/?q=Туса&type=event&city_id={city_id}&future=1&offset=0&count=10&access_token={config.vk_bot_token2}&v={config.vk_api}"
    response = requests.get(url_all)
    data = response.json()
    
    if 'response' in data and 'items' in data['response']:
        for event in data['response']['items']:
            arr_link_vk_all.append(event['screen_name'])
    time.sleep(0.5)
    return arr_link_vk_all

async def get_group_info(group_ids):
    logging.info('get_group_info')
    group_info = []
    for i in range(0, len(group_ids), 500):
        groupIds = ','.join(group_ids[i:i + 500])
        url = f"https://api.vk.com/method/groups.getById/?group_ids={groupIds}&fields=start_date,finish_date,description,city&access_token={config.vk_bot_token2}&v={config.vk_api}"
        response = requests.get(url)
        data = response.json()
        if 'response' in data:
            group_info.extend(data['response'])
        time.sleep(1)
    return group_info

async def main():
    vk_session = auth()
    longpoll = VkLongPoll(vk_session)   
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            message_text = event.text
            user_id = event.user_id
            logging.info(f"Received message: {message_text} from user: {user_id}")

            if message_text.lower() == "начать":
                vk_session.method('messages.send', {
                    'user_id': user_id,
                    'message': 'Привет! Введи город на русском, поищем в нём тусы',
                    'random_id': 0
                })
            else:
                logging.info('main not start')
                logging.info(message_text)
                if message_text in cities_csv:
                    city = message_text
                    logging.info(city)
                    events = read_csv('events.csv')
                    grouped_events = group_events_by_weekday(events, city, 1)
                    formatted_message = format_message(grouped_events, 1)
                    logging.info(len(events))
                    logging.info(222)
                    logging.info(len(formatted_message))

                    i = 0
                    for message in formatted_message:
                        if i == 0:
                            logging.info(309)
                            logging.info(message)
                            vk_session.method('messages.send', {
                                'user_id': user_id,
                                'message': f"{city}\n\n" + message,
                                'random_id': 0,
                                'disable_web_page_preview': 1
                            })
                        else:
                            vk_session.method('messages.send', {
                                'user_id': user_id,
                                'message': message,
                                'random_id': 0,
                                'disable_web_page_preview': 1
                            })
                        i = i + 1
                    vk_session.method('messages.send', {
                        'user_id': user_id,
                        'message': f"Выше тусы города {city} \n\n#тусынавыхи Остальное clck.ru/3KMog8",
                        'random_id': 0,
                        'disable_web_page_preview': 1
                    })

if __name__ == '__main__':
    asyncio.run(main())

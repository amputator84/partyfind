import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import asyncio
import aiohttp
import time
from datetime import datetime, timedelta
import config
import logging
import traceback

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ------------------ Асинхронные HTTP-запросы ------------------
async def vk_api_request_async(session, url, params=None, semaphore=None, max_retries=3):
    """Асинхронный GET-запрос к API ВК с повторными попытками и семафором."""
    if semaphore:
        async with semaphore:
            return await _fetch_with_retries(session, url, params, max_retries)
    else:
        return await _fetch_with_retries(session, url, params, max_retries)

async def _fetch_with_retries(session, url, params, max_retries):
    for attempt in range(max_retries):
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.warning(f"HTTP {response.status} при запросе {url}, попытка {attempt+1}")
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.warning(f"Ошибка запроса (попытка {attempt+1}/{max_retries}): {e}")
        if attempt < max_retries - 1:
            await asyncio.sleep(2 ** attempt)  # экспоненциальная задержка
    logger.error(f"Не удалось выполнить запрос {url} после {max_retries} попыток")
    return None

# ------------------ Синхронные обёртки для VK API (авторизация, отправка сообщений) ------------------
def auth():
    try:
        vk_session = vk_api.VkApi(token=config.vk_token)
        return vk_session
    except Exception as e:
        logger.error(f"Ошибка авторизации: {e}\n{traceback.format_exc()}")
        raise

# ------------------ Асинхронные функции для получения данных ------------------
async def get_city_ids_async(cities, session, semaphore):
    city_ids = []
    for city in cities:
        params = {
            'access_token': config.vk_token_all,
            'v': '5.131',
            'country_id': 1,
            'q': city,
            'count': 1
        }
        url = 'https://api.vk.com/method/database.getCities'
        data = await vk_api_request_async(session, url, params, semaphore)
        if data and 'response' in data and 'items' in data['response'] and data['response']['items']:
            city_ids.append(data['response']['items'][0])
        elif data and 'error' in data:
            logger.error(f"Ошибка API при поиске города '{city}': {data['error']}")
            return 'error'
        else:
            logger.info(f"Город '{city}' не найден")
            return 'empty'
        await asyncio.sleep(0.2)  # небольшая задержка между запросами городов
    return city_ids

async def get_events_async(city_id, city_name, event_ses, vk_ses, session, semaphore):
    arr_link_vk_all = []
    try:
        vk_ses.method('messages.send', {
            'user_id': event_ses.user_id,
            'message': f"Идёт поиск тус города {city_name}",
            'random_id': 0
        })
    except Exception as e:
        logger.error(f"Не удалось отправить сообщение пользователю {event_ses.user_id}: {e}")

    # Создаём задачи для всех слов
    tasks = []
    for word in config.arr_word:
        params = {
            'q': word,
            'type': 'event',
            'city_id': city_id,
            'future': 1,
            'count': 999,
            'access_token': config.vk_token_all,
            'v': config.vk_api
        }
        url = 'https://api.vk.com/method/groups.search'
        tasks.append(vk_api_request_async(session, url, params, semaphore))
    
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    for idx, data in enumerate(responses):
        word = config.arr_word[idx]
        if isinstance(data, Exception):
            logger.error(f"Ошибка для слова '{word}': {data}")
            continue
        if data and 'response' in data and 'items' in data['response']:
            items = data['response']['items']
            for event in items:
                arr_link_vk_all.append(event['screen_name'])
            logger.info(f"Получены события для города {city_name} (id {city_id}), слово '{word}', найдено {len(items)} групп")
        else:
            logger.info(f"Нет событий для слова '{word}' в городе {city_name}")
    return arr_link_vk_all

async def get_group_info_async(group_ids, session, semaphore):
    group_info = []
    # Разбиваем на чанки по 500
    for i in range(0, len(group_ids), 500):
        chunk = group_ids[i:i+500]
        groupIds = ','.join(chunk)
        url = f"https://api.vk.com/method/groups.getById/"
        params = {
            'group_ids': groupIds,
            'fields': 'start_date,finish_date,description,city',
            'access_token': config.vk_token_all,
            'v': config.vk_api
        }
        data = await vk_api_request_async(session, url, params, semaphore)
        if data and 'response' in data:
            group_info.extend(data['response'])
            logger.info(f"Загружена информация о {len(data['response'])} группах (чанк {i//500 + 1})")
        else:
            logger.error(f"Ошибка при загрузке чанка {i//500 + 1}: {data}")
            # Пробуем загрузить каждый элемент по отдельности
            for gid in chunk:
                single_params = {
                    'group_id': gid,
                    'fields': 'start_date,finish_date,description,city',
                    'access_token': config.vk_token_all,
                    'v': config.vk_api
                }
                single_url = 'https://api.vk.com/method/groups.getById'
                single_data = await vk_api_request_async(session, single_url, single_params, semaphore)
                if single_data and 'response' in single_data:
                    group_info.extend(single_data['response'])
                await asyncio.sleep(0.2)
        await asyncio.sleep(0.5)  # пауза между чанками
    return group_info

# ------------------ Синхронные функции обработки данных (не требуют асинхронности) ------------------
def group_events_by_weekday(events, city, week):
    filtered_events = [event for event in events if event['city'].lower() == city.lower()]
    for event in filtered_events:
        event['start_date'] = datetime.strptime(event['start_date'], '%d.%m.%Y')

    if week == 1:
        today = datetime.utcnow()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        filtered_events = [event for event in filtered_events if start_of_week <= event['start_date'] <= end_of_week]

    grouped_events = {}
    for event in filtered_events:
        weekday = event['start_date'].strftime('%A')
        if weekday not in grouped_events:
            grouped_events[weekday] = []
        grouped_events[weekday].append(event)
    return grouped_events

def format_message(grouped_events, week):
    message_parts = []
    if week == 1:
        for weekday, events in grouped_events.items():
            message_parts.append(f"{config.day_of_week_rus[weekday]} {events[0]['start_date'].strftime('%d.%m.%Y')}")
            for event in events:
                message_parts.append(f"[{event['screen_name_link']}|{event['name']}]")
            message_parts.append("")
    else:
        all_dates = []
        for events in grouped_events.values():
            for event in events:
                all_dates.append(event['start_date'])
        if not all_dates:
            return []
        min_date = min(all_dates)
        max_date = max(all_dates)
        current_date = min_date
        while current_date <= max_date:
            events_today = []
            for events in grouped_events.values():
                for event in events:
                    if event['start_date'].date() == current_date.date():
                        events_today.append(event)
            if events_today:
                weekday = current_date.strftime('%A')
                message_parts.append(f"{config.day_of_week_rus[weekday]} {current_date.strftime('%d.%m.%Y')}")
                for event in events_today:
                    message_parts.append(f"[{event['screen_name_link']}|{event['name']}]")
                message_parts.append("")
            current_date += timedelta(days=1)
    
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

# ------------------ Асинхронная основная логика для одного города ------------------
async def get_events_from_city_web_async(city, week, event_ses, vk_ses):
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(3)
        city_find = await get_city_ids_async([city], session, semaphore)
        if city_find == 'error':
            return 'ERROR'  # ошибка API
        if city_find == 'empty':
            return 'CITY_NOT_FOUND'  # город не существует
        city_id = city_find[0]['id']
        city_name = city_find[0]['title']
        
        arr_link_vk_all = await get_events_async(city_id, city_name, event_ses, vk_ses, session, semaphore)
        if not arr_link_vk_all:
            logger.info(f"В городе {city_name} не найдено групп-событий по ключевым словам")
            return False
        
        group_info = await get_group_info_async(arr_link_vk_all, session, semaphore)
        end_urls = []
        unique_events = set()
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
                logger.error(f"Ошибка обработки события {event.get('id', 'unknown')}: {e}")
                continue
        end_urls.sort(key=lambda x: (x['city'], datetime.strptime(x['start_date'], '%d.%m.%Y')))
        if not end_urls:
            logger.info(f"В городе {city_name} нет будущих мероприятий после фильтрации")
            return False
        grouped_events = group_events_by_weekday(end_urls, city_name, week)
        formatted_messages = format_message(grouped_events, week)
        if not end_urls:
            return False  # мероприятий нет
        return formatted_messages  # список сообщений

# ------------------ Синхронный обработчик сообщений (запускает асинхронную функцию) ------------------
def main():
    try:
        vk_session = auth()
        longpoll = VkLongPoll(vk_session)
        logger.info("Бот успешно запущен и слушает сообщения")
    except Exception as e:
        logger.critical(f"Не удалось запустить бота: {e}")
        return

    for event in longpoll.listen():
        try:
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                message_text = event.text
                user_id = event.user_id

                if message_text.lower() == "начать":
                    vk_session.method('messages.send', {
                        'user_id': user_id,
                        'message': 'Привет! Введи город на русском, поищем в нём тусы',
                        'random_id': 0
                    })
                    logger.info(f"Пользователь {user_id} отправил команду 'начать'")
                else:
                    city = message_text.strip()
                    logger.info(f"Пользователь {user_id} запросил город '{city}'")
                    
                    # Запускаем асинхронный поиск
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(
                            get_events_from_city_web_async(city, 0, event, vk_session)
                        )
                    finally:
                        loop.close()
                    
                    if result == 'CITY_NOT_FOUND':
                        vk_session.method('messages.send', {
                            'user_id': user_id,
                            'message': f"Не нашли город {city}, введите другой",
                            'random_id': 0,
                            'disable_web_page_preview': 1
                        })
                    elif result == 'ERROR':
                        vk_session.method('messages.send', {
                            'user_id': user_id,
                            'message': f"Какая-то ошибка, напиши админу",
                            'random_id': 0,
                            'disable_web_page_preview': 1
                        })
                    elif result is False:
                        vk_session.method('messages.send', {
                            'user_id': user_id,
                            'message': f"В '{city}' тус нет",
                            'random_id': 0,
                            'disable_web_page_preview': 1
                        })
                    else:
                        # result – список сообщений
                        for i, message in enumerate(result):
                            if i == 0:
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
                        vk_session.method('messages.send', {
                            'user_id': user_id,
                            'message': f"Выше тусы города {city} \n\n#тусынавыхи Остальное clck.ru/3KMog8",
                            'random_id': 0,
                            'disable_web_page_preview': 1
                        })
                        logger.info(f"Пользователю {user_id} отправлено {len(result)} сообщений")
        except Exception as e:
            logger.error(f"Необработанная ошибка при обработке события: {e}\n{traceback.format_exc()}")
            try:
                vk_session.method('messages.send', {
                    'user_id': event.user_id,
                    'message': 'Произошла внутренняя ошибка, попробуйте позже.',
                    'random_id': 0
                })
            except:
                pass

if __name__ == '__main__':
    main()
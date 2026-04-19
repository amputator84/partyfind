import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import requests
import time
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading
import config
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Словарь для отслеживания активных поисков пользователей
active_searches = {}
# Блокировка для потокобезопасного доступа к общим данным
lock = threading.Lock()
# Счетчик городов для каждого пользователя
user_city_count = defaultdict(int)
# Текущий обрабатываемый город для пользователя
user_current_city = {}
# Очередь запросов (пользователь, город, event)
request_queue = deque()
# Флаг работы обработчика очереди
queue_processor_running = False
# Поток обработчика очереди
queue_thread = None
# Флаг, указывающий, что сейчас обрабатывается запрос
is_processing = False

def auth():
    vk_session = vk_api.VkApi(token=config.vk_token)
    return vk_session

def get_city_ids(cities):
    city_ids = []
    for city in cities:
        response = requests.get(
            'https://api.vk.com/method/database.getCities',
            params={
                'access_token': config.vk_token_all,
                'v': '5.131',
                'country_id': 1,
                'q': city,
                'count': 1
            }
        )
        data = response.json()
        if 'response' in data and 'items' in data['response'] and len(data['response']['items']) > 0:
            city_ids.append(data['response']['items'][0])
        else:
            if 'error' in data:
                return 'error'
            elif (len(data['response']['items']) == 0):
                return 'empty'
            else:
                return 'error'
        time.sleep(0.5)
    return city_ids

def get_events(city_id, city_name, event_ses, vk_ses):
    arr_link_vk_all = []
    vk_ses.method('messages.send', {
        'user_id': event_ses.user_id,
        'message': f"Идёт поиск тус города {city_name}",
        'random_id': 0
    })
    for word in config.arr_word: # ['1', ' ', 'а']:
        url_all = f"https://api.vk.com/method/groups.search/?q={word}&type=event&city_id={city_id}&future=1&offset=0&count=999&access_token={config.vk_token_all}&v={config.vk_api}"
        response = requests.get(url_all)
        data = response.json()
        if 'response' in data and 'items' in data['response']:
            for event in data['response']['items']:
                arr_link_vk_all.append(event['screen_name'])
        time.sleep(0.5)
    return arr_link_vk_all

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

def get_events_from_city_web(city, week, event_ses, vk_ses):
    end_urls = []
    unique_events = set()
    city_find = get_city_ids([city])
    if city_find == 'error' or city_find == 'empty':
        return False
    city_id = city_find[0]['id']
    city_name = city_find[0]['title']
    arr_link_vk_all = get_events(city_id, city_name, event_ses, vk_ses)
    if len(arr_link_vk_all) > 0:
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
            except Exception:
                pass
        end_urls.sort(key=lambda x: (x['city'], datetime.strptime(x['start_date'], '%d.%m.%Y')))
        if not end_urls:
            return False
        grouped_events = group_events_by_weekday(end_urls, city_name, week)
        formatted_message = format_message(grouped_events, week)
        return formatted_message
    else:
        return False

def process_user_city(user_id, city, event, vk_session):
    """Обработка одного города для пользователя"""
    global is_processing
    try:
        logger.info(f"Пользователь {user_id} ищет город: {city}")
        events = get_events_from_city_web(city, 0, event, vk_session)
        
        if events is False:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': f"Не нашли тусы в городе {city}, попробуйте другой",
                'random_id': 0,
                'disable_web_page_preview': 1
            })
        else:
            i = 0
            for message in events:
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
                i += 1
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': f"Выше тусы города {city} \n\n#тусынавыхи Остальное clck.ru/3KMog8",
                'random_id': 0,
                'disable_web_page_preview': 1
            })
            logger.info(f"Пользователь {user_id} получил результаты для города: {city}")
    except Exception as e:
        logger.error(f"Ошибка при обработке города {city} для пользователя {user_id}: {e}")
    finally:
        with lock:
            # Снимаем флаг активного поиска
            active_searches[user_id] = False
            user_current_city.pop(user_id, None)
            
            # Уменьшаем счетчик городов
            if user_id in user_city_count:
                user_city_count[user_id] -= 1
                if user_city_count[user_id] <= 0:
                    del user_city_count[user_id]
            
            # Снимаем флаг обработки
            is_processing = False

def queue_processor(vk_session):
    """Фоновый обработчик очереди - обрабатывает строго по одному запросу"""
    global queue_processor_running, is_processing
    
    while queue_processor_running:
        user_data = None
        
        with lock:
            # Берем следующий запрос только если сейчас ничего не обрабатывается
            if not is_processing and request_queue:
                user_data = request_queue.popleft()
                is_processing = True
        
        if user_data:
            user_id, city, event = user_data
            
            with lock:
                active_searches[user_id] = True
                user_current_city[user_id] = city
            
            # Обрабатываем запрос в том же потоке (синхронно)
            process_user_city(user_id, city, event, vk_session)
            
            # Отправляем уведомление следующему в очереди
            with lock:
                if request_queue:
                    next_user_id = request_queue[0][0]
                    # Можно отправить уведомление следующему пользователю
                    try:
                        vk_session.method('messages.send', {
                            'user_id': next_user_id,
                            'message': f'Погнали...',
                            'random_id': 0
                        })
                    except:
                        pass
        
        time.sleep(0.5)  # Небольшая задержка между запросами

def start_queue_processor(vk_session):
    """Запуск фонового обработчика очереди"""
    global queue_processor_running, queue_thread
    
    if not queue_processor_running:
        queue_processor_running = True
        queue_thread = threading.Thread(target=queue_processor, args=(vk_session,))
        queue_thread.daemon = True
        queue_thread.start()
        logger.info("Обработчик очереди запущен")

def main():
    vk_session = auth()
    longpoll = VkLongPoll(vk_session)
    
    # Запускаем фоновый обработчик очереди
    start_queue_processor(vk_session)
    
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            message_text = event.text
            user_id = event.user_id

            if message_text.lower() == "начать":
                logger.info(f"Пользователь {user_id} отправил команду 'начать'")
                vk_session.method('messages.send', {
                    'user_id': user_id,
                    'message': 'Привет! Введи город на русском, поищем в нём тусы',
                    'random_id': 0
                })
                continue

            # Проверяем, не превышен ли лимит городов
            with lock:
                city_count = user_city_count.get(user_id, 0)
            
            if city_count >= 2:
                vk_session.method('messages.send', {
                    'user_id': user_id,
                    'message': 'Подождите загрузки всех городов для вас и повторите запрос',
                    'random_id': 0
                })
                logger.info(f"Пользователь {user_id} превысил лимит городов (2)")
                continue

            # Проверяем, есть ли у пользователя активный поиск
            with lock:
                is_active = active_searches.get(user_id, False)
                current_city = user_current_city.get(user_id, 'неизвестного города')
            
            if is_active:
                vk_session.method('messages.send', {
                    'user_id': user_id,
                    'message': f'Пока ищем тусы города {current_city}',
                    'random_id': 0
                })
                logger.info(f"Пользователь {user_id} пытался ввести новый город, пока идет поиск {current_city}")
                continue

            city_find = get_city_ids([message_text])
            if city_find == 'empty':
                vk_session.method('messages.send', {
                    'user_id': user_id,
                    'message': f"Не нашли город {message_text}, введите другой",
                    'random_id': 0,
                    'disable_web_page_preview': 1
                })
            elif city_find == 'error':
                vk_session.method('messages.send', {
                    'user_id': user_id,
                    'message': f"Какая-то ошибка, напиши админу",
                    'random_id': 0,
                    'disable_web_page_preview': 1
                })
            else:
                city = city_find[0]['title']
                
                with lock:
                    # Увеличиваем счетчик городов
                    user_city_count[user_id] = user_city_count.get(user_id, 0) + 1
                    
                    # Добавляем в очередь
                    request_queue.append((user_id, city, event))
                    queue_position = len(request_queue)
                    
                    # Если это первый в очереди и ничего не обрабатывается - не отправляем сообщение об ожидании
                    if queue_position == 1 and not is_processing:
                        pass  # Обработчик сам возьмет и отправит уведомление
                    else:
                        # Отправляем сообщение об ожидании
                        wait_message = f'Очередь {queue_position}'
                        if is_processing:
                            wait_message += ' Ждём...'
                        vk_session.method('messages.send', {
                            'user_id': user_id,
                            'message': wait_message,
                            'random_id': 0
                        })
                
                logger.info(f"Пользователь {user_id} добавил город {city} в очередь. Позиция: {queue_position}")

if __name__ == '__main__':
    main()
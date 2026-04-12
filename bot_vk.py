import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import asyncio
import aiohttp
from datetime import datetime, timedelta
import config
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class AsyncVkBot:
    def __init__(self):
        self.vk_session = None
        self.loop = None
        self.thread = None
        self.active_searches = set()  # Множество пользователей с активным поиском
        
    def auth(self):
        self.vk_session = vk_api.VkApi(token=config.vk_token)
        return self.vk_session
    
    async def get_city_id(self, session, city):
        """Асинхронное получение ID города"""
        url = 'https://api.vk.com/method/database.getCities'
        params = {
            'access_token': config.vk_token_all,
            'v': '5.131',
            'country_id': 1,
            'q': city,
            'count': 1
        }
        
        try:
            async with session.get(url, params=params) as response:
                data = await response.json()
                if 'response' in data and 'items' in data['response'] and len(data['response']['items']) > 0:
                    return data['response']['items'][0]
                elif 'error' in data:
                    return 'error'
                elif len(data['response']['items']) == 0:
                    return 'empty'
                else:
                    return 'error'
        except Exception as e:
            logger.error(f"Ошибка при получении города {city}: {e}")
            return 'error'
    
    async def get_city_ids(self, cities):
        """Асинхронное получение ID нескольких городов"""
        async with aiohttp.ClientSession() as session:
            tasks = [self.get_city_id(session, city) for city in cities]
            results = await asyncio.gather(*tasks)
            
            for result in results:
                if result == 'error':
                    return 'error'
                elif result == 'empty':
                    return 'empty'
            return results
    
    async def get_events_for_word(self, session, city_id, word):
        """Асинхронное получение событий для одного слова"""
        url = f"https://api.vk.com/method/groups.search/"
        params = {
            'q': word,
            'type': 'event',
            'city_id': city_id,
            'future': 1,
            'offset': 0,
            'count': 999,
            'access_token': config.vk_token_all,
            'v': config.vk_api
        }
        
        try:
            async with session.get(url, params=params) as response:
                data = await response.json()
                if 'response' in data and 'items' in data['response']:
                    return [event['screen_name'] for event in data['response']['items']]
                return []
        except Exception as e:
            logger.error(f"Ошибка при получении событий для слова {word}: {e}")
            return []
    
    async def get_events(self, city_id, city_name, user_id):
        """Асинхронное получение всех событий города"""
        arr_link_vk_all = []
        
        # Отправляем сообщение о начале поиска
        await self.send_message_async(user_id, f"Идёт поиск тус города {city_name}")
        
        async with aiohttp.ClientSession() as session:
            words = config.arr_word #['1', ' ', 'а'] #config.arr_word
            tasks = [self.get_events_for_word(session, city_id, word) for word in words]
            results = await asyncio.gather(*tasks)
            
            for result in results:
                arr_link_vk_all.extend(result)
        
        return arr_link_vk_all
    
    async def get_group_info_batch(self, session, group_ids):
        """Асинхронное получение информации о группе для одного батча"""
        groupIds = ','.join(group_ids)
        url = f"https://api.vk.com/method/groups.getById/"
        params = {
            'group_ids': groupIds,
            'fields': 'start_date,finish_date,description,city',
            'access_token': config.vk_token_all,
            'v': config.vk_api
        }
        
        try:
            async with session.get(url, params=params) as response:
                data = await response.json()
                if 'response' in data:
                    return data['response']
                return []
        except Exception as e:
            logger.error(f"Ошибка при получении информации о группах: {e}")
            return []
    
    async def get_group_info(self, group_ids):
        """Асинхронное получение информации о всех группах"""
        group_info = []
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(0, len(group_ids), 500):
                batch = group_ids[i:i + 500]
                tasks.append(self.get_group_info_batch(session, batch))
            
            results = await asyncio.gather(*tasks)
            for result in results:
                group_info.extend(result)
        
        return group_info
    
    def group_events_by_weekday(self, events, city, week):
        """Группировка событий по дням недели"""
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
    
    def format_message(self, grouped_events, week):
        """Форматирование сообщения"""
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
                return [""]
            
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
    
    async def send_message_async(self, user_id, message):
        """Асинхронная отправка сообщения"""
        try:
            # Запускаем синхронный метод в executor
            await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.vk_session.method('messages.send', {
                    'user_id': user_id,
                    'message': message,
                    'random_id': 0,
                    'disable_web_page_preview': 1
                })
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")
    
    async def process_city(self, city_text, user_id):
        """Асинхронная обработка одного города"""
        # Проверяем, есть ли уже активный поиск для этого пользователя
        if user_id in self.active_searches:
            logger.info(f"Пользователь {user_id} попытался запустить поиск {city_text}, но уже есть активный поиск")
            await self.send_message_async(user_id, "Поиск {city_text} ещё не закончен")
            return
        
        try:
            # Добавляем пользователя в активные поиски
            self.active_searches.add(user_id)
            
            # Получаем ID города
            city_find = await self.get_city_ids([city_text])
            
            if city_find == 'empty':
                await self.send_message_async(user_id, f"Не нашли город {city_text}, введите другой")
                return
            elif city_find == 'error':
                await self.send_message_async(user_id, f"Какая-то ошибка, напиши админу")
                return
            
            city = city_find[0]['title']
            city_id = city_find[0]['id']

            logger.info(f"Начинаем поиск для города: {city}, пользователь: {user_id}")
            
            # Получаем события
            arr_link_vk_all = await self.get_events(city_id, city, user_id)
            
            if len(arr_link_vk_all) > 0:
                group_info = await self.get_group_info(arr_link_vk_all)
                unique_events = set()
                end_urls = []
                
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
                        logger.error(f"Ошибка при обработке события: {e}")
                        pass
                
                end_urls.sort(key=lambda x: (x['city'], datetime.strptime(x['start_date'], '%d.%m.%Y')))
                
                if not end_urls:
                    await self.send_message_async(user_id, f"Не нашли тусы в городе {city}, попробуйте другой")
                else:
                    grouped_events = self.group_events_by_weekday(end_urls, city, 0)
                    formatted_messages = self.format_message(grouped_events, 0)
                    
                    # Отправляем результаты
                    for i, message in enumerate(formatted_messages):
                        if i == 0:
                            await self.send_message_async(user_id, f"{city}\n\n" + message)
                        else:
                            await self.send_message_async(user_id, message)
                    
                    await self.send_message_async(user_id, f"Выше тусы города {city} \n\n#тусынавыхи Остальное clck.ru/3KMog8")
            else:
                await self.send_message_async(user_id, f"Не нашли тусы в городе {city}, попробуйте другой")
                
        except Exception as e:
            logger.error(f"Ошибка при обработке города {city_text}: {e}")
            await self.send_message_async(user_id, f"Произошла ошибка при поиске города {city_text}")
        finally:
            # Удаляем пользователя из активных поисков
            self.active_searches.discard(user_id)
            logger.info(f"Завершен поиск для города: {city_text}, пользователь: {user_id}")
    
    def run_async_loop(self):
        """Запуск асинхронного event loop в отдельном потоке"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
    
    def start_bot(self):
        """Запуск бота"""
        self.auth()
        longpoll = VkLongPoll(self.vk_session)
        
        # Создаем event loop в отдельном потоке
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.run_async_loop, daemon=True)
        self.thread.start()
        
        logger.info("Бот запущен и готов к работе")
        
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                message_text = event.text
                user_id = event.user_id
                
                if message_text.lower() == "начать":
                    logger.info(f"Пользователь {user_id} отправил команду 'начать'")
                    # Синхронная отправка приветственного сообщения
                    self.vk_session.method('messages.send', {
                        'user_id': user_id,
                        'message': 'Привет! Введи город на русском, поищем в нём тусы',
                        'random_id': 0
                    })
                else:
                    # Запускаем обработку города асинхронно
                    logger.info(f"Пользователь {user_id} запросил город: {message_text}")
                    asyncio.run_coroutine_threadsafe(
                        self.process_city(message_text, user_id),
                        self.loop
                    )

def main():
    bot = AsyncVkBot()
    bot.start_bot()

if __name__ == '__main__':
    main()
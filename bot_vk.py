import vk_api  # 11.9.9
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import logging
import requests
import time
import asyncio
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
class Config:
    vk_token_all = '123'
    vk_token_all2 = '234'
    vk_api = '5.131'
    city_id = 99

config = Config()

def auth():
    vk_session = vk_api.VkApi(token=config.vk_token_all)
    return vk_session

def create_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Кнопка 1', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Кнопка 2', color=VkKeyboardColor.NEGATIVE)
    return keyboard.get_keyboard()

def get_events(city_id):
    arr_link_vk_all = []
    url_all = f"https://api.vk.com/method/groups.search/?q=Туса&type=event&city_id={city_id}&future=1&offset=0&count=10&access_token={config.vk_token_all2}&v={config.vk_api}"
    response = requests.get(url_all)
    data = response.json()
    
    if 'response' in data and 'items' in data['response']:
        for event in data['response']['items']:
            arr_link_vk_all.append(event['screen_name'])
    time.sleep(0.5)
    return arr_link_vk_all

async def get_group_info(group_ids):
    logging.info('Fetching group info')
    group_info = []
    for i in range(0, len(group_ids), 500):
        groupIds = ','.join(group_ids[i:i + 500])
        url = f"https://api.vk.com/method/groups.getById/?group_ids={groupIds}&fields=start_date,finish_date,description,city&access_token={config.vk_token_all2}&v={config.vk_api}"
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
            message_text = event.text.lower()
            user_id = event.user_id
            logging.info(f"Received message: {message_text} from user: {user_id}")

            if message_text == "начать":
                keyboard = create_keyboard()
                vk_session.method('messages.send', {
                    'user_id': user_id,
                    'message': 'Выберите кнопку:',
                    'keyboard': keyboard,
                    'random_id': 0
                })
            elif message_text == "кнопка 1":
                vk_session.method('messages.send', {
                    'user_id': user_id,
                    'message': 'Вы нажали кнопку 1!',
                    'random_id': 0
                })
            elif message_text == "кнопка 2":
                logging.info(81)
                arr_link_vk_all = get_events(config.city_id)
                logging.info(arr_link_vk_all)
                group_info = await get_group_info(arr_link_vk_all)
                logging.info(group_info)
                if group_info:
                    event_details = "\n".join(f"{info['name']}: {info.get('description', 'Нет описания')}" for info in group_info)
                    vk_session.method('messages.send', {
                        'user_id': user_id,
                        'message': f"Список событий в Новосибирске на сегодня:\n{event_details}",
                        'random_id': 0
                    })
                else:
                    vk_session.method('messages.send', {
                        'user_id': user_id,
                        'message': 'Не удалось получить события.',
                        'random_id': 0
                    })

if __name__ == '__main__':
    asyncio.run(main())

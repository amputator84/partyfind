import requests
import csv
import time
from datetime import datetime
import config

vkToken = config.vk_token_all
vkApi = '5.131'
arrWord = config.arr_word
# cities = config.cities # включаем все города для формирования CSV
cities = [c for c in config.cities if c not in config.big_cities]

def get_city_ids(cities):
    city_ids = []
    for city in cities:
        response = requests.get('https://api.vk.com/method/database.getCities', params={
            'access_token': vkToken, 'v': vkApi, 'country_id': 1, 'q': city, 'count': 1
        })
        try:
            data = response.json()
            if data.get('response', {}).get('items'):
                city_ids.append({'name': city, 'id': data['response']['items'][0]['id']})
            else:
                print(f"Город '{city}' не найден.")
        except Exception as e:
            print(f"Ошибка {e}")
        time.sleep(0.5)
    return city_ids

def get_events(city_id):
    arrLinkVkAll = []
    for word in arrWord:
        response = requests.get('https://api.vk.com/method/groups.search', params={
            'q': word, 'type': 'event', 'city_id': city_id, 'future': 1,
            'offset': 0, 'count': 999, 'access_token': vkToken, 'v': vkApi
        })
        data = response.json()
        if data.get('response', {}).get('items'):
            arrLinkVkAll.extend(e['screen_name'] for e in data['response']['items'])
        time.sleep(0.5)
    return arrLinkVkAll

def get_group_info(group_ids):
    group_info = []
    for i in range(0, len(group_ids), 500):
        response = requests.get('https://api.vk.com/method/groups.getById', params={
            'group_ids': ','.join(group_ids[i:i+500]),
            'fields': 'start_date,finish_date,description,city',
            'access_token': vkToken, 'v': vkApi
        })
        data = response.json()
        if data.get('response'):
            group_info.extend(data['response'])
        time.sleep(1)
    return group_info

def main():
    endUrls, unique_events = [], set()
    print(f"Города: {cities}")
    
    for city_data in get_city_ids(cities):
        print(f"Обработка: {city_data['name']} (ID: {city_data['id']})")
        
        for event in get_group_info(get_events(city_data['id'])):
            try:
                start_date = event.get('start_date')
                city = event.get('city', {})
                
                if not (start_date and start_date > int(datetime.now().timestamp()) and city.get('title')):
                    continue
                name = event.get('name', '').replace('[', ' ').replace(']', ' ').replace('{', ' ').replace('}', ' ').replace('|', ' ')
                description = event.get('description', '').replace('[', ' ').replace(']', ' ').replace('{', ' ').replace('}', ' ').replace('|', ' ')
                start_date_formatted = datetime.fromtimestamp(start_date).strftime('%d.%m.%Y')
                screen_name = f'=HYPERLINK("https://vk.com/{event["screen_name"]}";"{event["screen_name"]}")'
                
                event_tuple = (city['title'], name, screen_name, start_date_formatted, description)
                if event_tuple not in unique_events:
                    unique_events.add(event_tuple)
                    endUrls.append({
                        'city': city['title'], 'name': name, 'screen_name': screen_name,
                        'start_date': start_date_formatted,
                        'screen_name_link': event.get('screen_name'), 'description': description
                    })
            except Exception as e:
                print(f"Ошибка: {e}")

    endUrls.sort(key=lambda x: (x['city'], datetime.strptime(x['start_date'], '%d.%m.%Y')))
    
    with open('events.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['city', 'name', 'screen_name', 'start_date', 'screen_name_link', 'description'], delimiter=';')
        writer.writeheader()
        writer.writerows(endUrls)

if __name__ == "__main__":
    main()
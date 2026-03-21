import requests
import csv
import time
from datetime import datetime
import config

vkToken = config.vk_token_all
vkApi = '5.131'
arrWord = config.arr_word
cities = config.cities
#arrWord = ['a','1']
#cities = ['Москва','Санкт-Петербург']

# Функция для получения ID городов
def get_city_ids(cities):
    city_ids = []
    for city in cities:
        response = requests.get(
            'https://api.vk.com/method/database.getCities',
            params={
                'access_token': vkToken,
                'v': vkApi,
                'country_id': 1,
                'q': city,
                'count': 1
            }
        )
        try:
            data = response.json()
            if 'response' in data and 'items' in data['response'] and len(data['response']['items']) > 0:
                city_ids.append(data['response']['items'][0]['id'])
            else:
                print(f"Город '{city}' не найден.")
        except Exception as e:
            print(f"Ошибка {e}")
        time.sleep(0.5)
    return city_ids

# Функция для получения событий
def get_events(city_id):
    arrLinkVkAll = []
    for word in arrWord:
        urlAll = f"https://api.vk.com/method/groups.search/?q={word}&type=event&city_id={city_id}&future=1&offset=0&count=999&access_token={vkToken}&v={vkApi}"
        print(f"Запрос URL: {urlAll}")
        response = requests.get(urlAll)
        data = response.json()
        if 'response' in data and 'items' in data['response']:
            for event in data['response']['items']:
                arrLinkVkAll.append(event['screen_name'])
        time.sleep(0.5)
    return arrLinkVkAll

# Функция для получения информации о группах
def get_group_info(group_ids):
    group_info = []
    for i in range(0, len(group_ids), 500):
        groupIds = ','.join(group_ids[i:i + 500])
        url = f"https://api.vk.com/method/groups.getById/?group_ids={groupIds}&fields=start_date,finish_date,description,city&access_token={vkToken}&v={vkApi}"
        print(f"Запрос URL: {url}")
        response = requests.get(url)
        data = response.json()
        if 'response' in data:
            group_info.extend(data['response'])
        time.sleep(1)
    return group_info

# Основная логика
def main():
    endUrls = []
    unique_events = set()
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

    # Сортировка и запись в CSV
    endUrls.sort(key=lambda x: (x['city'], datetime.strptime(x['start_date'], '%d.%m.%Y')))
    with open('events.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['city', 'name', 'screen_name', 'start_date', 'screen_name_link', 'description']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        for row in endUrls:
            writer.writerow(row)

if __name__ == "__main__":
    main()
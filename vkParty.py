import requests
import time
import datetime
import json
import csv

# https://oauth.vk.com/authorize?client_id=8143518&scope=groups&redirect_uri=http%3A%2F%2Foauth.vk.com%2Fblank.html&display=page&response_type=token
access_token = '123'

# Так как в ограничении ВК берутся первые 999 записей, придётся искать не по пробелу, а по разным словам в цикле. Так затронется больше тус
search_query = ['рок', 'тусовка', ' ', 'квартирник', 'концерт', 'выступление', 'фест', 'шоу', 'дискотека', 'вечеринка',
                'посиделки', 'баттл', 'флешмоб', 'выставка', 'выпускной', 'карнавал']
cities = [1, 2, 25, 49, 64, 97, 99, 104, 144]
arr_all = []
arr_all_fin = []
events_url = ''

for city_id in cities:
    print(events_url)
    # ставим паузы, чтоб не ДДОСить
    time.sleep(0.3)
    for q in search_query:
        time.sleep(0.3)
        #print(str(city_id) + ' - ' + q)
        events_url = f'https://api.vk.com/method/groups.search?q={q}&access_token={access_token}&v=5.199&type=event&city_id={city_id}&future=1&count=999'
        response = requests.get(events_url)
        data = response.json()

        if 'error' in data:
            print(f'Ошибка при запросе списка мероприятий и событий: {data["error"]["error_msg"]}')
            exit()

        for group in data['response']['items']:
            # print(city_id)
            group['city'] = city_id
            arr_all.append(group)
print('Количество тус = ' + str(len(arr_all)))
# Удаление дубликатов
arr_all = list({group['id']: group for group in arr_all}.values())

# Сортировка по city
arr_all.sort(key=lambda x: x['city'])
print('Количество тус2 = ' + str(len(arr_all)))

group_ids = [str(group['id']) for group in arr_all]
# режем по 500 записей. Ограничение ВК
group_ids_chunks = [group_ids[i:i + 500] for i in range(0, len(group_ids), 500)]

for group_ids_chunk in group_ids_chunks:
    time.sleep(0.2)
    group_ids_str = ','.join(group_ids_chunk)
    group_info_url = f'https://api.vk.com/method/groups.getById?group_ids={group_ids_str}&fields=start_date,description,city&access_token={access_token}&v=5.199'
    # print(group_info_url)
    # print()
    response = requests.get(group_info_url)
    data = response.json()
    # print('Количество общее = ' + str(len(data['response']['groups'])))

    # Фильтрация элементов, у которых есть поле "city"
    filtered_groups = [group for group in data['response']['groups'] if 'city' in group]

    # Сортировка по значениям "city.title" и "start_date"
    # sorted_groups = sorted(filtered_groups, key=lambda x: (x['city']['title'], x['start_date']))

    # Вывод отсортированного массива
    # print(sorted_groups)

    # Вывод результатов
    city_name2 = ''
    for group_info in filtered_groups:
        city_name = group_info['city']['title']
        group_name = group_info['name']
        group_screen_name = group_info['screen_name']
        if (int(group_info['start_date']) < 0):
            continue
        start_date = datetime.datetime.fromtimestamp(group_info['start_date'])
        group_description = group_info['description']
        if city_name != city_name2:
            # print(f'Город - {city_name}')
            city_name2 = city_name
        # print(f'name - {group_name}')
        # print(f'{group_name} https://vk.com/event{group_id} {start_date.day}.{start_date.month}.{start_date.year}')
        # print(f'description - {group_description}')
        # print()
        arr_all_fin.append({
            "name_rus": city_name,
            "name": group_name,
            "link": '=HYPERLINK("https://vk.com/' + str(group_screen_name) + '")',  # TODO club/event
            "date_format": f'{start_date.day}.{start_date.month}.{start_date.year}',
            "clear": "",
            "description": group_description,
        })

arr_all_fin = sorted(arr_all_fin, key=lambda x: (x['name_rus'], x['date_format']))
# Имя файла для сохранения
file_name = 'output.csv'

# Запись данных в CSV файл
with open(file_name, mode='w', encoding='utf-8', newline='') as csv_file:
    fieldnames = ['name_rus', 'name', 'link', 'date_format', 'clear', 'description']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=';')

    writer.writeheader()
    for row in arr_all_fin:
        writer.writerow(row)

print(f'Массив данных был успешно выгружен в файл {file_name}')

"""
Есть скрипт на python:

1. Придумываем массив фраз для поиска событий - "search_query". Допустим "рок,тусовка,пати,квартирник,концерт,выступление"
2. Собираем ID нужных городов из вконтакте - cities = [99,1,2,144]
3. Делаем цикл по городам
4. Делаем цикл по названию событий search_query
5. Получаем список событий по api, зная токен и выводим их на экран:
import requests
import time
access_token = '123'
search_query = ['рок', 'тусовка', 'пати', 'квартирник', 'концерт', 'выступление']
cities = [99, 1, 2, 144]
arr_all = []

for city_id in cities:
    time.sleep(0.2)
    for q in search_query:
        time.sleep(0.1)
        events_url = f'https://api.vk.com/method/groups.search?q={q}&access_token={access_token}&v=5.199&type=event&city_id={city_id}&future=1&count=999'
        response = requests.get(events_url)
        data = response.json()

        if 'error' in data:
            print(f'Ошибка при запросе списка мероприятий и событий: {data["error"]["error_msg"]}')
            exit()

        for group in data['response']['items']:
            group['city'] = city_id
            arr_all.append(group)

# Удаление дубликатов
arr_all = list({group['id']: group for group in arr_all}.values())

# Сортировка по city
arr_all.sort(key=lambda x: x['city'])

Нужно модифицировать скрипт. Из arr_all брать по 500 записей и искать дополнительную информацию по ID (в https://api.vk.com/method/groups.getById?group_ids=187569150,225562379&fields=start_date,description&access_token={access_token}&v=5.199), записанным через запятую в group_ids. Дополнительные поля - start_date,description.
По итогу нужно сформировать список, выглядящий так:

Город 1
name - Название события
description - описание события
start_date - дата начала события

Город 2
name - Название события
description - описание события
start_date - дата начала события

События в рамках города отсортированы по дате.

Вывести итоговый список на экран.

"""

"""Пытаюсь на питоне написать проверку на наличие поля city в структуре JSON, но получаю ошибку "KeyError: 'city'". Как сделать проверку на наличие поля, чтоб не выводились ошибки?

   Структура JSON:
   {
     "response": {
       "groups": [
         {
           "id": 11,
           "city": {
             "id": 1,
             "title": "Москва"
           },
           "description": "П11",
           "name": "SajiM?",
           "start_date": 1728651600
         },
         {
           "id": 12,
           "city": {
             "id": 99,
             "title": "Новосибирск"
           },
           "description": "П11",
           "name": "SajiM?",
           "start_date": 1731301200
         },
         {
           "id": 22,
           "description": "Рr",
           "screen_name": "jak",
           "start_date": 1731501200
         },
         {
           "id": 33,
           "city": {
             "id": 1,
             "title": "Москва"
           },
           "description": "П11",
           "name": "SajiM?",
           "start_date": 1731321200
         },
       ],
       "profiles": []
     }
   }

   По итогу должен сформироваться отсортированный по city.title и start_date массив.
"""

"""
database.getCities
1,2,25,49,64,97,99,104,144
1 - Москва
2 - Санкт-Петербург
99 - Новосибирск
49 - Екатеринбург
97 - Новокузнецк
25 - Барнаул
64 - Кемерово
144 - Томск
104 - Омск
"""
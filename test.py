# Скрипт, добавляющий тусы в СФО за сегодняшний день отложенным постом
import csv
import datetime
import urllib.parse
import re

TOKEN = ''
GROUP_ID = '172727080'
cityNotOutArray = ['Москва', 'Санкт-Петербург', 'Екатеринбург']
DATE_TOMORROW = '1722978490'
city_rows = {}
regEx = r'\"(.*?)\"'
with open('output.csv', 'r', encoding='utf-8') as file:
    reader = csv.DictReader(file, delimiter=';')
    today = datetime.date.today().strftime('%d.%m.%Y')

    for row in reader:
        #print(row['\ufeffname_rus'])
        if row['\ufeffname_rus'] not in cityNotOutArray and row['date_format'] == today:
            city = row['\ufeffname_rus']
            event_name = row['name']
            event_link = re.search(regEx, row['link']).group(1)
            city_rows[city] = f'[{event_link}|{event_name}]'

message_long = today + '\n\n'
for city, events in city_rows.items():
    message_long += city + '\n'
    for event in events:
        message_long += event
    message_long += '\n\n'

print(message_long)

encoded_message_long = urllib.parse.quote(message_long)

longLink = f'https://api.vk.com/method/wall.post?v=5.131&owner_id=-{GROUP_ID}&access_token={TOKEN}&from_group=1&message={encoded_message_long}&publish_date={DATE_TOMORROW}'

print(longLink)

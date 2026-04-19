import csv
import datetime
import sys
import requests
import config
from collections import defaultdict

target_date = datetime.datetime.strptime(sys.argv[1], '%d.%m.%Y') if len(sys.argv) > 1 else datetime.datetime.now()
date_str = target_date.strftime('%d.%m.%Y')
weekday_rus = config.day_of_week_rus[target_date.strftime('%A')]

def escape_vk_mention(text):
    return text.replace('(', '❨').replace(')', '❩').replace('[', '⟦').replace(']', '⟧').replace('|', '｜')

cities_events = defaultdict(list)
with open('events.csv', 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f, delimiter=';'):
        if row['start_date'] == date_str and row['city'] not in ['Москва', 'Санкт-Петербург', 'Екатеринбург']:
            cities_events[row['city']].append(f"@{row['screen_name_link']} ({escape_vk_mention(row['name'])})")

cities = sorted(cities_events.keys())
if hasattr(config, 'first_city') and config.first_city in cities_events:
    cities.insert(0, cities.pop(cities.index(config.first_city)))

lines = [f"{weekday_rus} {date_str}"]
for city in cities:
    lines.extend([f"\n{city}"] + cities_events[city])
text = "\n".join(lines + ["\n#тусынавыхи Остальное clck.ru/3KMog8"])

print(f"{text}\n\n[DEBUG] Длина текста: {len(text)} символов")
print(requests.post('https://api.vk.com/method/wall.post', data={
    'v': '5.107', 'owner_id': f'-{config.owner_id}', 'access_token': config.vk_token,
    'from_group': 1, 'message': text
}).json())
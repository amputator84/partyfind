import csv
import datetime
import urllib.parse
from collections import defaultdict
import requests
import config

# Текущая дата
now = datetime.datetime.now()
date_str = now.strftime('%d.%m.%Y')
weekday_rus = config.day_of_week_rus[now.strftime('%A')]

# Группировка событий по городам
cities_events = defaultdict(list)

with open('events.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        if row['start_date'] == date_str and row['city'] not in ['Москва', 'Санкт-Петербург', 'Екатеринбург']:
            cities_events[row['city']].append(f"[{row['screen_name_link']}|{row['name']}]")

# Если нет событий — выходим
if not cities_events:
    print("Нет событий на сегодня")
    exit()

# Сортировка городов: заданный первым, остальные по алфавиту
if hasattr(config, 'first_city') and config.first_city in cities_events:
    cities = [config.first_city] + sorted(c for c in cities_events if c != config.first_city)
else:
    cities = sorted(cities_events.keys())

# Формирование текста поста
lines = [f"{weekday_rus} {date_str}"]
for city in cities:
    lines.append(f"\n{city}")
    lines.extend(cities_events[city])
lines.append("\n#тусынавыхи Остальное clck.ru/3KMog8")
text = "\n".join(lines)

print(text)

# Отправка в VK
tomorrow = int((now + datetime.timedelta(days=1)).timestamp())
url = f'https://api.vk.com/method/wall.post?v=5.107&owner_id=-{config.owner_id}&access_token={config.vk_token}&from_group=1&message={urllib.parse.quote(text)}&publish_date={tomorrow}'

response = requests.get(url)
print(response.json())
import csv
import datetime
import urllib.parse
from collections import defaultdict
import requests
import config
import sys

# Определяем дату
if len(sys.argv) > 1:
    target_date = datetime.datetime.strptime(sys.argv[1], '%d.%m.%Y')
else:
    target_date = datetime.datetime.now()

date_str = target_date.strftime('%d.%m.%Y')
weekday_rus = config.day_of_week_rus[target_date.strftime('%A')]

def escape_vk_mention(text):
    """
    Экранирует проблемные символы в названии для корректного отображения
    упоминаний в VK. Заменяет скобки и другие спецсимволы на похожие Unicode-символы.
    """
    # Заменяем круглые скобки
    text = text.replace('(', '❨')  # U+2768 - маленькая левая скобка
    text = text.replace(')', '❩')  # U+2769 - маленькая правая скобка
    
    # Заменяем квадратные скобки
    text = text.replace('[', '⟦')  # U+27E6 - левая белая квадратная скобка
    text = text.replace(']', '⟧')  # U+27E7 - правая белая квадратная скобка
    
    # Альтернативные варианты для квадратных скобок (раскомментируйте если нужно)
    # text = text.replace('[', '【')  # U+3010 - левая черная лентикулярная скобка
    # text = text.replace(']', '】')  # U+3011 - правая черная лентикулярная скобка
    # text = text.replace('[', '〔')  # U+3014 - левая скобка-черепаха
    # text = text.replace(']', '〕')  # U+3015 - правая скобка-черепаха
    
    # Заменяем вертикальную черту (pipe)
    text = text.replace('|', '｜')  # U+FF5C - полноширинная вертикальная черта
    # Альтернативы для вертикальной черты:
    # text = text.replace('|', '¦')  # U+00A6 - прерывистая вертикальная черта
    # text = text.replace('|', '∣')  # U+2223 - математический знак "делит"
    # text = text.replace('|', '│')  # U+2502 - элемент псевдографики (жирнее)
    
    return text

# Группировка событий по городам
cities_events = defaultdict(list)

with open('events.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        if row['start_date'] == date_str and row['city'] not in ['Москва', 'Санкт-Петербург', 'Екатеринбург']:
            # Используем короткий формат упоминания: @clubXXXX (Название)
            club_id = row['screen_name_link']
            safe_name = escape_vk_mention(row['name'])
            event_text = f"@{club_id} ({safe_name})"
            cities_events[row['city']].append(event_text)

# Сортировка городов
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
print(f"\n[DEBUG] Длина текста: {len(text)} символов")

# Отправка в VK (БЕЗ attachments)
url = 'https://api.vk.com/method/wall.post'
params = {
    'v': '5.107',
    'owner_id': f'-{config.owner_id}',
    'access_token': config.vk_token,
    'from_group': 1,
    'message': text
}

response = requests.post(url, data=params)  # Используем POST вместо GET с параметрами
print(response.json())
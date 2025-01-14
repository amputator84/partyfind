import csv
import datetime
import urllib.parse
import requests

# Получаем текущую дату
current_date = datetime.datetime.utcnow()
current_weekday = current_date.strftime('%A')
current_date_str = current_date.strftime('%d.%m.%Y')
today_date = current_date.strftime('%d.%m.%Y')  # Получаем дату в формате ДД.ММ.ГГГГ

# Словарь для хранения событий по дате
events_by_date = {}

# Открываем файл events.csv
with open('events.csv', 'r', encoding='utf-8') as file:
    reader = csv.DictReader(file, delimiter=';')
    
    # Проходим по строкам файла
    for row in reader:
        # Проверяем, совпадает ли дата события с текущей
        if row['start_date'] == current_date_str and row['city'] not in ['Москва', 'Санкт-Петербург', 'Екатеринбург']:
            city = row['city']
            screen_name_link = row['screen_name_link']
            name = row['name']
            
            # Формируем запись события
            event_entry = f"[{screen_name_link}|{name}]"
            
            # Добавляем событие в словарь
            if current_date_str not in events_by_date:
                events_by_date[current_date_str] = {}
            if city not in events_by_date[current_date_str]:
                events_by_date[current_date_str][city] = []
            events_by_date[current_date_str][city].append(event_entry)

# Выводим результаты
for date, cities in events_by_date.items():
    weekday_russian = {
        'Monday': 'Понедельник',
        'Tuesday': 'Вторник',
        'Wednesday': 'Среда',
        'Thursday': 'Четверг',
        'Friday': 'Пятница',
        'Saturday': 'Суббота',
        'Sunday': 'Воскресенье'
    }
    
    # Формируем текст для публикации
    txtUrl = ""
    for city, names in events_by_date.items():
        txtUrl += f"{weekday_russian[current_weekday]} {date}\n"
    
    for city, events in cities.items():
        txtUrl += f"\n{city}\n"  # Перенос строки перед названием города
        for event in events:
            txtUrl += f"{event}\n"
    
    txtUrl += '\n'
    txtUrl += "#тусынавыхи Остальное goo.gl/Df6FBQ"
    
# Кодируем текст для URL
encoded_txtUrl = urllib.parse.quote(txtUrl)

# Задаем параметры для запроса к API ВКонтакте
tomorrow = int((current_date + datetime.timedelta(days=1)).timestamp())
vkToken = '234'
url = f'https://api.vk.com/method/wall.post?v=5.107&owner_id=-172727080&access_token={vkToken}&from_group=1&message={encoded_txtUrl}&publish_date={tomorrow}'

# Отправляем запрос
response = requests.get(url)
print(response.json())
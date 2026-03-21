import csv
import datetime
import urllib.parse
import requests
import config

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
        # Проверяем, совпадает ли дата события с текущей и город не из списка больших
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
    # Словарь для перевода дней недели (можно взять из config, если он там есть)
    # Если в config нет day_of_week_rus, оставляем локальный
    try:
        weekday_russian = config.day_of_week_rus
    except AttributeError:
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
    txtUrl = f"{weekday_russian[current_weekday]} {date}\n"
    
    # Сортируем города: если задан first_city, он будет первым
    if hasattr(config, 'first_city') and config.first_city != '':
        # Создаем список городов, где first_city на первом месте
        city_names = list(cities.keys())
        # Убираем first_city из списка, если он там есть, чтобы потом добавить первым
        if config.first_city in city_names:
            city_names.remove(config.first_city)
            sorted_cities = [config.first_city] + sorted(city_names)
        else:
            sorted_cities = sorted(city_names)
    else:
        sorted_cities = sorted(cities.keys())
    
    for city in sorted_cities:
        events = cities[city]
        txtUrl += f"\n{city}\n"  # Перенос строки перед названием города
        for event in events:
            txtUrl += f"{event}\n"
    
    txtUrl += '\n'
    txtUrl += "#тусынавыхи Остальное clck.ru/3KMog8"
    print(txtUrl)

# Кодируем текст для URL
encoded_txtUrl = urllib.parse.quote(txtUrl)

# Задаем параметры для запроса к API ВКонтакте
tomorrow = int((current_date + datetime.timedelta(days=1)).timestamp())
url = f'https://api.vk.com/method/wall.post?v=5.107&owner_id=-{config.owner_id}&access_token={config.vk_token}&from_group=1&message={encoded_txtUrl}&publish_date={tomorrow}'

# Отправляем запрос
response = requests.get(url)
print(response.json())
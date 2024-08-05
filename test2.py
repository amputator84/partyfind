import csv
import datetime
import urllib.parse

TOKEN = '123'
GROUP_ID = '172727080'
cityNotOutArray = ['Москва', 'Санкт-Петербург', 'Екатеринбург']
DATE_TOMORROW = '1722978490'
# Открываем файл CSV
with open('output.csv', 'r', encoding='utf-8') as file:
    reader = csv.DictReader(file, delimiter=';')
    # Определяем текущий день
    today = datetime.date.today().strftime('%d.%m.%Y')

    # Создаем массив для хранения строк по городам
    city_rows = {}
    # Читаем строки из файла CSV
    for row in reader:
        # Проверяем, что дата соответствует текущему дню
        if row['date_format'] == today:
            # Проверяем, что город не находится в списке исключений
            city = row['name_rus']
            event_name = row['name']
            event_link = row['link']

            # Добавляем строку в массив для данного города
            #if city not in city_rows:
            #    city_rows[city] = []
            city_rows[city].append(f'[{event_link}|{event_name}]')

# Формируем строку MESSAGE_LONG
message_long = today + '\n\n'
for city, events in city_rows.items():
    message_long += city + '\n'
    for event in events:
        message_long += event + '\n'
    message_long += '\n'

#print(message_long)
#print('/n/n/n')

# Кодируем строку MESSAGE_LONG для использования в URL
encoded_message_long = urllib.parse.quote(message_long)

# Формируем итоговую ссылку longLink
longLink = f'https://api.vk.com/method/wall.post?v=5.131&owner_id=-{GROUP_ID}&access_token={TOKEN}&from_group=1&message={encoded_message_long}&publish_date={DATE_TOMORROW}'

# Выводим итоговую ссылку
print(longLink)

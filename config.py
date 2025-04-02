# Токен для бота. Даётся при создании бота в @BotFather
api_token = '123'
# токен для поста. Настраивается в паблике https://vk.com/your_public?act=tokens
vk_token = '123'
# токен для сбора тус по городам из https://oauth.vk.com/authorize?client_id={config.client_id}&scope=groups&redirect_uri=http%3A%2F%2Foauth.vk.com%2Fblank.html&display=page&response_type=token&scope=offline
vk_token_all = '123'
# Версия VK API
vk_api = '5.131'
# Слова для поиска тус
arr_word = ['й','ц','у','к','е','н','г','ш','щ','з','х','ф','в','а','п','р','о','л','д','ж','э','я','ч','с','м','и','т','б','.',',','q',' ','q','w','e','r','t','y','u','i','o','p','a','s','d','f','g','h','j','k','l','z','x','c','v','b','n','m','1','2','3','4','5','6','7','8','9','0']
# Города для поиска тус
cities = ['Абакан','Искитим','Новосибирск','Барнаул','Томск','Омск','Кемерово','Новокузнецк','Красноярск','Междуреченск','Новоалтайск','Горно-Алтайск','Шерегеш','Бердск','Москва','Санкт-Петербург','Екатеринбург']
# Города, не входящие в выгрузку get_post из csv
big_cities = ['Москва', 'Санкт-Петербург', 'Екатеринбург']
# Параметр группы для wall.post. Можно посмотреть тут https://dev.vk.com/ru/method/groups.getById
owner_id = '123'
# ID приложения для редиректа. Создаётся тут https://dev.vk.com/ru/admin/apps-list. С него же берётся vk_token_all. Изменение - https://vk.com/editapp?id={config.client_id}&section=options
client_id = '123'

day_of_week_rus = {
    'Monday': 'Понедельник',
    'Tuesday': 'Вторник',
    'Wednesday': 'Среда',
    'Thursday': 'Четверг',
    'Friday': 'Пятница',
    'Saturday': 'Суббота',
    'Sunday': 'Воскресенье'
}

# ID пользователя. Можно подглядеть в @getmyid_bot
me = 123
<?php
ini_set('error_reporting', E_ALL);
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
ini_set('max_execution_time', 500);
header('Content-Type: text/html; charset=utf-8');
require_once "config.php";
$days = array('ВОСКРЕСЕНЬЕ', 'ПОНЕДЕЛЬНИК', 'ВТОРНИК', 'СРЕДА', 'ЧЕТВЕРГ', 'ПЯТНИЦА', 'СУББОТА');
$sysDateFormat = date("d.m.Y", date("U"));
$dayNow = $days[(date('w'))].' '.$sysDateFormat;
$tomorrow = mktime(0, 0, 0, date("m"), date("d") + 1, date("Y"));
$q = "select c.name_rus,
             e.name,
             e.vk,
             case when c.name_rus = 'Новосибирск' then 0 else 1 end ORD
        from events e
        left join cities c on c.id = e.id_city
       where to_char(e.date,'dd.mm.yyyy') = '$sysDateFormat'
	     and c.id not in (1,2,49)
       order by ORD, c.name_rus asc";
$row = pg_query($q);
$city = '';
$cityNew = '';
$txt = "$dayNow \n\n";
while ($r = pg_fetch_assoc($row)) {
    $city = $r['name_rus'];
    if ($city != $cityNew) {
        $cityNew = "\n$city\n";
    } else {
        $cityNew = '';
    }
    $name = htmlspecialchars(strip_tags(preg_replace("[\]|\||\]|\$|amp;|\"|&|#|quot;]", '', $r['name'])), ENT_QUOTES);
    $link = $r['vk'];
    $txt .= "$cityNew [$link|$name]\n";
    $cityNew = $city;
}
$txt = $txt . "\n #тусынавыхи Остальное goo.gl/Df6FBQ";
$txtUrl = urlencode($txt);
/*
 *
 * https://dev.vk.com/api/access-token/implicit-flow-community
 * Создаём приложение https://vk.com/editapp
 * Получаем ID приложения
 * Вводим с нашим ID
 * https://oauth.vk.com/authorize?client_id=6212084&scope=docs,wall,offline&redirect_uri=http%3A%2F%2Foauth.vk.com%2Fblank.html&display=page&response_type=token
*/
$vkToken2 = '123';
$url = 'https://api.vk.com/method/wall.post?v=5.107&owner_id=-172727080&access_token=' . $vkToken2 . '&from_group=1&message=' . $txtUrl . '&publish_date=' . $tomorrow;
echo $url;
//echo "<br/>";
//echo strlen($txtUrl);
//echo "<br/>";
try {
    file_get_contents($url);
    echo 'Пост добавлен';
    return 'Пост добавлен';
} catch (Exception $e) {
    echo $e;
    return $e;
}
?>
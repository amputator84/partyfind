<?php
require_once "config.php";
require_once "db.php";

class WorkFlow
{
    public function send($txt, $keyboard = null, $user_id){
        $request_params = array(
            'message' => $txt,
            'peer_id' => $user_id,
            'access_token' => TOKEN,
            'v' => '5.126',
            'keyboard' => $keyboard,
            'random_id' => '0'
        );
        //error_log("+++++++++++++++".$txt);
        $get_params = http_build_query($request_params);
        //$request_params = 'message='.$txt.'&peer_id='.$user_id.'&access_token='.TOKEN.'&v=5.126&keyboard='.$keyboard.'&random_id=0';
        error_log("+++++++++++++++".$get_params);
        file_get_contents('https://api.vk.com/method/messages.send?'. $get_params);
        echo('ok');
    }
    /* Список городов */
    public function getCities($user_id, $ret = 0){
        $keyboard = array();
        array_push($keyboard, '[{"action": {"type": "text","label": "Все города","payload": "{\"button\": \"all_cities\"}"},"color":"secondary"}]'); //{\"button\": \"all_cities\"}
        $i = 1;
        $q = "select t.name_rus
                    from (select distinct c.name_rus
                            from events e
                            left join places p on p.id = e.id_place
                            join cities c on (c.id = p.id_city or c.id = e.id_city)) t
                   order by t.name_rus";
        $res = pg_query($q);
        while ($row = pg_fetch_assoc($res)) {
            $r = $row['name_rus'];
            array_push($keyboard, '[{"action": {"type": "text","label": "'.$r.'","payload": "{\"button\": \"id_city'.$i.'\"}"},"color":"secondary"}]');
            $i++;
        }
        $keyboard = implode(',', $keyboard);
        $keyboard = '{"one_time":false,"buttons":['.$keyboard.']}';
        if ($ret == 1) return $keyboard;
        $token = TOKEN;
        $user_info = json_decode(file_get_contents("https://api.vk.com/method/users.get?user_ids={$user_id}&access_token={$token}&v=5.126"));
        $user_name = $user_info->response[0]->first_name;
        $this->send('Выберите город тус, '.$user_name, $keyboard, $user_id);
    }

    /* Поиск тус в заданном городе */
    public function getEventFromCity($txt, $all = 0, $user_id){
        echo 1;
        error_log("getEventFromCity = ".$txt);
        $q = "select count(1) cnt from cities c where ((upper(c.name_rus) = upper('".$txt."') and 0 = '".$all."') or (1 = '".$all."'))";
        $res = pg_query($q);
        $cnt = pg_fetch_result($res,0,'cnt');
        echo 55;
        if ($cnt == 0) return false;
        else {
            echo 58;
            if ($all != 1) {
                $order = "e.date,c.name_rus";
            } else {
                $order = "c.name_rus,e.date";
            }

            $query = "select to_char(e.date,'dd.mm.yyyy') date,
                             e.name event_name,
                             e.link_vk event_vk,
                             c.name_rus
                        from events e
                        left join places p on p.id = e.id_place
                        join cities c on (c.id = p.id_city or c.id = e.id_city)
                       where ((upper(c.name_rus) = upper('".$txt."') and 0 = '".$all."') or (1 = '".$all."'))
                       order by ".$order." asc";
            echo $query;
            echo "\n";
            $result = pg_query($query);
            $txtOut = 'Тусы в городе '.$txt.'';//перенос строки
            $city = '';
            $city2 = '';
            while ($row = pg_fetch_assoc($result)) {
                //urlencode
                $city2 = $row['name_rus'];
                $left = '[';
                $mid = '|';
                $right = ']';//__________
                $name = htmlspecialchars(strip_tags(preg_replace("[\]|\||\]|\$|amp;|\"|&|#|quot;]", '', $row['event_name'])), ENT_QUOTES);
                if ($city != $city2 && $all == 1){
                    $city = $city2;
                    $txtOut = $txtOut.$city2."";//перенос строки
                }
                $txtOut = $txtOut.$row['date'].' - '.$left.$row['event_vk'].$mid.$name.$right."";//перенос строки
            }
            $keyboardBack = $this->getCities($user_id, 1);
            /*if (strlen($txtOut) >= 1000) {
                $arr2 = '';
                $arr = explode('__________', $txtOut);
                for ($i = 0; $i < count($arr); $i++) {
                    if (strlen($arr2) >= 500) {
                        $this->send($arr2, $keyboardBack, $user_id);
                        $arr2 = '';
                    }
                    $arr2 = $arr2 . $arr[$i];
                }
                $this->send($arr2, $keyboardBack, $user_id);
            } else {
                $this->send(str_replace('__________','',$txtOut), $keyboardBack, $user_id);
            }*/
            echo $txtOut;
            error_log("getEventFromCity = ".$txtOut);
            $this->send('qweqwe'.date("Y-m-d H:i:s"), null, $user_id);//$keyboardBack
        }
    }
}
?>
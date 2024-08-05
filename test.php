<?php
    require_once "config.php";
    require_once "db.php";
    require_once "workflow.php";
    $workFlow = new WorkFlow();
//$t = '\u041d\u043e\u0432\u043e\u0441\u0438\u0431\u0438\u0440\u0441\u043a';
//echo preg_match('/./', 'Новосибирскю..');
//echo utf8_encode($t);
/*
 выберите город (getCity)
   Все города
   Новосибирск
   Барнаул
*/
//$workFlow->send('121212',null,5978179);
//$workFlow->getEventFromCity('Иркутск', 0, 5978179);
echo date("Y-m-d H:i:s");
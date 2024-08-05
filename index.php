<?php

define('CALLBACK_API_EVENT_CONFIRMATION', 'confirmation');
define('CALLBACK_API_EVENT_MESSAGE_NEW', 'message_new');

require_once 'config.php';
require_once 'workflow.php';
require_once 'db.php';

if (!isset($_REQUEST)) {
  exit;
}

callback_handleEvent();

function callback_handleEvent() {
  $event = _callback_getEvent();

  try {
    switch ($event['type']) {
      //Подтверждение сервера
      case CALLBACK_API_EVENT_CONFIRMATION:
        _callback_handleConfirmation();
        break;

      //Получение нового сообщения
      case CALLBACK_API_EVENT_MESSAGE_NEW:
        //_callback_handleMessageNew($event['object']);
      //bot_sendMessage(5978179);
          vkApi_messagesSend(5978179, 'Привет 1');
      _callback_okResponse();
        break;

      default:
        _callback_response('Unsupported event');
        break;
    }
  } catch (Exception $e) {
    echo $e;
  }

  _callback_okResponse();
}

function _callback_getEvent() {
  return json_decode(file_get_contents('php://input'), true);
}

function _callback_handleConfirmation() {
  _callback_response(CONFIRMATION_TOKEN);
}

function _callback_handleMessageNew($data) {
  $user_id = $data['user_id'];
  bot_sendMessage($user_id);
  _callback_okResponse();
}

function _callback_okResponse() {
  _callback_response('ok');
}

function _callback_response($data) {
  echo $data;
  exit();
}

function _vkApi_call($method, $params = array()) {
  $params['access_token'] = TOKEN;
  $params['v'] = VK_API_VERSION;

  $query = http_build_query($params);
  $url = VK_API_ENDPOINT.$method.'?'.$query;

  $curl = curl_init($url);
  curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
  $json = curl_exec($curl);
  $error = curl_error($curl);
  if ($error) {
    //log_error($error);
    throw new Exception("Failed {$method} request");
  }

  curl_close($curl);

  $response = json_decode($json, true);
  if (!$response || !isset($response['response'])) {
    //log_error($json);
    throw new Exception("Invalid response for {$method} request");
  }

  return $response['response'];
}

function vkApi_messagesSend($peer_id, $message) {
  return _vkApi_call('messages.send', array(
    'peer_id'    => $peer_id,
    'message'    => $message
  ));
}
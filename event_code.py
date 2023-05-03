import logging
import os
import requests
import urllib3

from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

SCHEME = os.getenv('SCHEME')
HOST = os.getenv('HOST')
PORT = os.getenv('PORT')
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')


def get_base_url():
    return '{}://{}:{}/servicesNS/{}/'.format(SCHEME, HOST, PORT, USERNAME)


def get_auth_url():
    app = 'system'
    return '{}{}/auth/login/'.format(get_base_url(), app)


def get_api_auth_answer(sess, auth_url):
    payload = {
        'username': USERNAME,
        'password': PASSWORD,
        'output_mode': 'json',
    }
    try:
        response = sess.post(auth_url, data=payload)
        if response.ok:
            logging.info(f'Получили ответ от API {auth_url}')
        else:
            logging.error(f'Не удалось получить ответ от API, '
                          f'код ошибки {response.status_code}')
            raise Exception(response.status_code)
    except Exception as e:
        logging.error(f'Недоступность эндпоинта, ошибка: {e}')
        raise Exception('Недоступность эндпоинта')
    return response.json()


def parse_session_key(response):
    try:
        sess_key = response.get('sessionKey')
        logging.info(f'Получили `sessionKey`: {sess_key}')
    except KeyError:
        logging.error('Отсутствие `sessionKey` в ответе API')
        raise KeyError('Нет ожидаемого ключа')
    headers = {
        'Authorization': 'Splunk {}'.format(sess_key),
    }
    return headers


def main():
    """Основная логика работы бота."""
    logging.basicConfig(
        level=logging.DEBUG,
        filename='log.log',
        format='%(asctime)s, %(levelname)s, %(message)s',
    )
    auth_url = get_auth_url()
    with requests.Session() as session:
        session.verify = False
        response = get_api_auth_answer(session, auth_url)
        headers = parse_session_key(response)
        session.headers.update(headers)
        logging.info('Установлены заголовки для всей сессии')


if __name__ == '__main__':
    main()

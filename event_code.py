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


def get_api_auth_answer(auth_url):
    payload = {
        'username': USERNAME,
        'password': PASSWORD,
        'output_mode': 'json',
    }
    try:
        response = requests.post(auth_url, data=payload, verify=False)
        if not response.ok:
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
    except KeyError:
        logging.error('Отсутствие `sessionKey` в ответе API')
        raise KeyError('Нет ожидаемого ключа')
    headers = {
        'Authorization': 'Splunk {}'.format(sess_key),
    }
    return headers


def set_headers(sess, headers):
    ...


def main():
    """Основная логика работы бота."""
    logging.basicConfig(
        level=logging.DEBUG,
        filename='log.log',
        format='%(asctime)s, %(levelname)s, %(message)s',
    )
    print(get_base_url())
    print(get_auth_url())
    auth_url = get_auth_url()
    response = get_api_auth_answer(auth_url)
    print(parse_session_key(response))


if __name__ == '__main__':
    main()
